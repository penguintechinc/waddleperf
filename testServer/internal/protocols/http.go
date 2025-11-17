package protocols

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"golang.org/x/net/http2"
)

type HTTPTestRequest struct {
	Target         string `json:"target"`
	Protocol       string `json:"protocol"`        // http1, http2, http3
	ProtocolDetail string `json:"protocol_detail"` // Alternative field name for compatibility
	Method         string `json:"method"`
	Timeout        int    `json:"timeout"` // seconds
}

type HTTPTestResult struct {
	Target         string  `json:"target"`
	Protocol       string  `json:"protocol"`
	StatusCode     int     `json:"status_code"`
	LatencyMS      float64 `json:"latency_ms"`
	TTFBMS         float64 `json:"ttfb_ms"`
	TotalTimeMS    float64 `json:"total_time_ms"`
	Success        bool    `json:"success"`
	Error          string  `json:"error,omitempty"`
	ConnectedProto string  `json:"connected_proto"`
}

func TestHTTP(req HTTPTestRequest) (*HTTPTestResult, error) {
	// Use ProtocolDetail if Protocol is empty (for compatibility)
	protocol := req.Protocol
	if protocol == "" {
		protocol = req.ProtocolDetail
	}
	// Default to http2 if still empty
	if protocol == "" {
		protocol = "http2"
	}

	// Ensure target has scheme
	target := req.Target
	if !strings.HasPrefix(target, "http://") && !strings.HasPrefix(target, "https://") {
		target = "https://" + target
	}

	result := &HTTPTestResult{
		Target:   target,
		Protocol: protocol,
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 30 * time.Second
	}

	var client *http.Client

	switch protocol {
	case "http1":
		client = &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
			},
		}
	case "http2":
		client = &http.Client{
			Timeout: timeout,
			Transport: &http2.Transport{
				TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
			},
		}
	case "http3":
		// TODO: Implement HTTP/3 when quic-go is stable
		return nil, fmt.Errorf("HTTP/3 not yet implemented")
	default:
		return nil, fmt.Errorf("unsupported protocol: %s", protocol)
	}

	method := req.Method
	if method == "" {
		method = "GET"
	}

	startTime := time.Now()

	httpReq, err := http.NewRequest(method, target, nil)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		return result, err
	}

	httpReq.Header.Set("User-Agent", "WaddlePerf-TestServer/1.0")

	resp, err := client.Do(httpReq)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0
		return result, err
	}
	defer resp.Body.Close()

	totalTime := time.Since(startTime)

	result.StatusCode = resp.StatusCode
	result.TotalTimeMS = float64(totalTime.Microseconds()) / 1000.0
	result.LatencyMS = result.TotalTimeMS // Simplified for now
	result.TTFBMS = result.TotalTimeMS    // Simplified for now
	result.Success = resp.StatusCode >= 200 && resp.StatusCode < 400
	result.ConnectedProto = resp.Proto

	return result, nil
}

func (r *HTTPTestResult) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}
