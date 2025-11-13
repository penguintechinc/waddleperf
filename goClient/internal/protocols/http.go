package protocols

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptrace"
	"time"

	"golang.org/x/net/http2"
)

type HTTPTestRequest struct {
	Target   string `json:"target"`
	Protocol string `json:"protocol"` // http1, http2, http3
	Method   string `json:"method"`
	Timeout  int    `json:"timeout"` // seconds
}

type HTTPTestResult struct {
	Target           string  `json:"target"`
	Protocol         string  `json:"protocol"`
	StatusCode       int     `json:"status_code"`
	LatencyMS        float64 `json:"latency_ms"`
	TTFBMS           float64 `json:"ttfb_ms"`
	DNSLookupMS      float64 `json:"dns_lookup_ms"`
	TCPConnectMS     float64 `json:"tcp_connect_ms"`
	TLSHandshakeMS   float64 `json:"tls_handshake_ms"`
	TotalTimeMS      float64 `json:"total_time_ms"`
	Success          bool    `json:"success"`
	Error            string  `json:"error,omitempty"`
	ConnectedProto   string  `json:"connected_proto"`
	ContentLengthKB  float64 `json:"content_length_kb"`
	TransferSpeedMBs float64 `json:"transfer_speed_mbs"`
}

func TestHTTP(req HTTPTestRequest) (*HTTPTestResult, error) {
	result := &HTTPTestResult{
		Target:   req.Target,
		Protocol: req.Protocol,
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 30 * time.Second
	}

	var transport http.RoundTripper

	switch req.Protocol {
	case "http1":
		transport = &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
			// Force HTTP/1.1
			TLSNextProto: make(map[string]func(authority string, c *tls.Conn) http.RoundTripper),
		}
	case "http2":
		transport = &http2.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
		}
	case "http3":
		// HTTP/3 requires quic-go library - not implemented yet
		return nil, fmt.Errorf("HTTP/3 not yet implemented")
	default:
		// Auto-detect
		transport = &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
		}
	}

	client := &http.Client{
		Timeout:   timeout,
		Transport: transport,
	}

	method := req.Method
	if method == "" {
		method = "GET"
	}

	// Detailed timing using httptrace
	var (
		dnsStart      time.Time
		dnsDuration   time.Duration
		connectStart  time.Time
		connectDone   time.Duration
		tlsStart      time.Time
		tlsDuration   time.Duration
		firstByte     time.Time
		requestStart  time.Time
		contentLength int64
	)

	trace := &httptrace.ClientTrace{
		DNSStart: func(_ httptrace.DNSStartInfo) {
			dnsStart = time.Now()
		},
		DNSDone: func(_ httptrace.DNSDoneInfo) {
			if !dnsStart.IsZero() {
				dnsDuration = time.Since(dnsStart)
			}
		},
		ConnectStart: func(_, _ string) {
			connectStart = time.Now()
		},
		ConnectDone: func(_, _ string, _ error) {
			if !connectStart.IsZero() {
				connectDone = time.Since(connectStart)
			}
		},
		TLSHandshakeStart: func() {
			tlsStart = time.Now()
		},
		TLSHandshakeDone: func(_ tls.ConnectionState, _ error) {
			if !tlsStart.IsZero() {
				tlsDuration = time.Since(tlsStart)
			}
		},
		GotFirstResponseByte: func() {
			firstByte = time.Now()
		},
	}

	requestStart = time.Now()

	httpReq, err := http.NewRequest(method, req.Target, nil)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		return result, err
	}

	httpReq = httpReq.WithContext(httptrace.WithClientTrace(httpReq.Context(), trace))
	httpReq.Header.Set("User-Agent", "WaddlePerf-GoClient/1.0")

	resp, err := client.Do(httpReq)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		result.TotalTimeMS = float64(time.Since(requestStart).Microseconds()) / 1000.0
		return result, err
	}
	defer resp.Body.Close()

	// Read response body to calculate transfer speed
	buf := make([]byte, 32*1024)
	totalBytes := int64(0)
	for {
		n, err := resp.Body.Read(buf)
		totalBytes += int64(n)
		if err != nil {
			break
		}
	}

	totalTime := time.Since(requestStart)
	contentLength = totalBytes

	result.StatusCode = resp.StatusCode
	result.TotalTimeMS = float64(totalTime.Microseconds()) / 1000.0
	result.DNSLookupMS = float64(dnsDuration.Microseconds()) / 1000.0
	result.TCPConnectMS = float64(connectDone.Microseconds()) / 1000.0
	result.TLSHandshakeMS = float64(tlsDuration.Microseconds()) / 1000.0

	if !firstByte.IsZero() {
		result.TTFBMS = float64(firstByte.Sub(requestStart).Microseconds()) / 1000.0
	} else {
		result.TTFBMS = result.TotalTimeMS
	}

	result.LatencyMS = result.TTFBMS
	result.Success = resp.StatusCode >= 200 && resp.StatusCode < 400
	result.ConnectedProto = resp.Proto
	result.ContentLengthKB = float64(contentLength) / 1024.0

	if totalTime.Seconds() > 0 {
		result.TransferSpeedMBs = (float64(contentLength) / 1024.0 / 1024.0) / totalTime.Seconds()
	}

	return result, nil
}

func (r *HTTPTestResult) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}
