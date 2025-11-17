package protocols

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/url"
	"strconv"
	"strings"
	"time"
)

type UDPTestRequest struct {
	Target         string `json:"target"`
	Protocol       string `json:"protocol"`        // raw, tls, dns
	ProtocolDetail string `json:"protocol_detail"` // Alternative field name for compatibility
	Port           int    `json:"port"`            // Optional port override
	Timeout        int    `json:"timeout"`
	Query          string `json:"query,omitempty"` // For DNS
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
	// Use ProtocolDetail if Protocol is empty (for compatibility)
	protocol := req.Protocol
	if protocol == "" {
		protocol = req.ProtocolDetail
	}
	// Default to dns if still empty
	if protocol == "" {
		protocol = "dns"
	}

	// Parse target to extract host and port
	target, err := parseUDPTarget(req.Target, req.Port, protocol)
	if err != nil {
		return nil, err
	}

	result := &UDPTestResult{
		Target:   target,
		Protocol: protocol,
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 5 * time.Second
	}

	switch protocol {
	case "raw":
		return testRawUDP(target, timeout, result)
	case "dns":
		return testDNS(target, req.Query, timeout, result)
	case "tls":
		// DTLS not commonly implemented in Go stdlib
		result.Error = "UDP+TLS (DTLS) not yet implemented"
		return result, fmt.Errorf(result.Error)
	default:
		result.Error = fmt.Sprintf("unsupported protocol: %s", protocol)
		return result, fmt.Errorf(result.Error)
	}
}

// parseUDPTarget extracts host:port from various input formats
func parseUDPTarget(target string, portOverride int, protocol string) (string, error) {
	// If target already has host:port format, use it
	if strings.Contains(target, ":") && !strings.Contains(target, "://") {
		return target, nil
	}

	// Try to parse as URL
	var host string
	var port int

	if strings.Contains(target, "://") {
		// Parse as URL
		u, err := url.Parse(target)
		if err != nil {
			return "", fmt.Errorf("invalid target URL: %v", err)
		}
		host = u.Hostname()
		if u.Port() != "" {
			port, _ = strconv.Atoi(u.Port())
		}
	} else {
		// Assume it's just a hostname
		host = target
	}

	// Use port override if provided
	if portOverride > 0 {
		port = portOverride
	}

	// If still no port, use defaults based on protocol
	if port == 0 {
		switch protocol {
		case "dns":
			port = 53
		case "raw":
			port = 161 // SNMP default, but UDP raw can be anything
		default:
			port = 161
		}
	}

	return fmt.Sprintf("%s:%d", host, port), nil
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
