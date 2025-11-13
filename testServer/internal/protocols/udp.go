package protocols

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"time"
)

type UDPTestRequest struct {
	Target   string `json:"target"`
	Protocol string `json:"protocol"` // raw, tls, dns
	Timeout  int    `json:"timeout"`
	Query    string `json:"query,omitempty"` // For DNS
}

type UDPTestResult struct {
	Target     string  `json:"target"`
	Protocol   string  `json:"protocol"`
	Success    bool    `json:"success"`
	LatencyMS  float64 `json:"latency_ms"`
	Error      string  `json:"error,omitempty"`
	RemoteAddr string  `json:"remote_addr"`
	Response   string  `json:"response,omitempty"`
}

func TestUDP(req UDPTestRequest) (*UDPTestResult, error) {
	result := &UDPTestResult{
		Target:   req.Target,
		Protocol: req.Protocol,
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 5 * time.Second
	}

	switch req.Protocol {
	case "raw":
		return testRawUDP(req.Target, timeout, result)
	case "dns":
		return testDNS(req.Target, req.Query, timeout, result)
	case "tls":
		// DTLS not commonly implemented in Go stdlib
		result.Error = "UDP+TLS (DTLS) not yet implemented"
		return result, fmt.Errorf(result.Error)
	default:
		result.Error = fmt.Sprintf("unsupported protocol: %s", req.Protocol)
		return result, fmt.Errorf(result.Error)
	}
}

func testRawUDP(target string, timeout time.Duration, result *UDPTestResult) (*UDPTestResult, error) {
	startTime := time.Now()

	conn, err := net.DialTimeout("udp", target, timeout)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0
		return result, err
	}
	defer conn.Close()

	// Send test packet
	testData := []byte("PING")
	conn.SetWriteDeadline(time.Now().Add(timeout))
	_, err = conn.Write(testData)
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("write error: %v", err)
		return result, err
	}

	// Try to read response (may timeout, which is ok for UDP)
	buf := make([]byte, 1024)
	conn.SetReadDeadline(time.Now().Add(timeout))
	n, err := conn.Read(buf)

	latency := time.Since(startTime)
	result.LatencyMS = float64(latency.Microseconds()) / 1000.0
	result.RemoteAddr = conn.RemoteAddr().String()

	if err != nil {
		// UDP might not get a response, which is still "successful" connectivity
		result.Success = true
		result.Response = "No response (expected for raw UDP)"
	} else {
		result.Success = true
		result.Response = fmt.Sprintf("Received %d bytes", n)
	}

	return result, nil
}

func testDNS(target, query string, timeout time.Duration, result *UDPTestResult) (*UDPTestResult, error) {
	if query == "" {
		query = "google.com"
	}

	startTime := time.Now()

	resolver := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{Timeout: timeout}
			return d.DialContext(ctx, "udp", target)
		},
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	ips, err := resolver.LookupHost(ctx, query)
	latency := time.Since(startTime)

	result.LatencyMS = float64(latency.Microseconds()) / 1000.0
	result.RemoteAddr = target

	if err != nil {
		result.Success = false
		result.Error = err.Error()
		return result, err
	}

	result.Success = true
	result.Response = fmt.Sprintf("Resolved %s to %d IPs: %v", query, len(ips), ips)

	return result, nil
}

func (r *UDPTestResult) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}
