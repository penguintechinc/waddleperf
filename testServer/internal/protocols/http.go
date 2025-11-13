package protocols

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
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
	result := &HTTPTestResult{
		Target:   req.Target,
		Protocol: req.Protocol,
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 30 * time.Second
	}

	var client *http.Client

	switch req.Protocol {
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
		return nil, fmt.Errorf("unsupported protocol: %s", req.Protocol)
	}

	method := req.Method
	if method == "" {
		method = "GET"
	}

	startTime := time.Now()

	httpReq, err := http.NewRequest(method, req.Target, nil)
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
