package protocols

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os/exec"
	"regexp"
	"strings"
	"time"
)

type HTTPTraceRequest struct {
	Target  string `json:"target"`
	Port    int    `json:"port"`
	Timeout int    `json:"timeout"`
}

type TCPTraceRequest struct {
	Target  string `json:"target"`
	Port    int    `json:"port"`
	Timeout int    `json:"timeout"`
}

type TracerouteRequest struct {
	Target  string `json:"target"`
	Timeout int    `json:"timeout"`
}

type UDPTraceRequest struct {
	Target  string `json:"target"`
	Port    int    `json:"port"`
	Timeout int    `json:"timeout"`
}

type TraceResult struct {
	Target    string   `json:"target"`
	Protocol  string   `json:"protocol"`
	Success   bool     `json:"success"`
	LatencyMS float64  `json:"latency_ms"`
	Hops      []string `json:"hops,omitempty"`
	Error     string   `json:"error,omitempty"`
	RouteInfo string   `json:"route_info,omitempty"`
}

// TestHTTPTrace performs an HTTP request with detailed trace information
func TestHTTPTrace(req HTTPTraceRequest) (*TraceResult, error) {
	result := &TraceResult{
		Target:   req.Target,
		Protocol: "http_trace",
	}

	// Ensure target has scheme
	target := req.Target
	if !strings.HasPrefix(target, "http://") && !strings.HasPrefix(target, "https://") {
		target = "https://" + target
	}

	// If port is specified and not default, append it
	if req.Port > 0 && req.Port != 443 && req.Port != 80 {
		u := target
		if strings.Contains(u, "://") {
			parts := strings.SplitN(u, "://", 2)
			if len(parts) == 2 {
				hostPath := parts[1]
				if !strings.Contains(hostPath, ":") {
					pathIdx := strings.Index(hostPath, "/")
					if pathIdx > 0 {
						target = fmt.Sprintf("%s://%s:%d%s", parts[0], hostPath[:pathIdx], req.Port, hostPath[pathIdx:])
					} else {
						target = fmt.Sprintf("%s://%s:%d", parts[0], hostPath, req.Port)
					}
				}
			}
		}
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 30 * time.Second
	}

	client := &http.Client{
		Timeout: timeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse // Don't follow redirects
		},
	}

	startTime := time.Now()

	httpReq, err := http.NewRequest("GET", target, nil)
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

	result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0
	result.Success = true

	// Collect trace information
	var hops []string
	hops = append(hops, fmt.Sprintf("HTTP/%s %s %s", resp.Proto, resp.Status, target))

	// Add header information
	if server := resp.Header.Get("Server"); server != "" {
		hops = append(hops, fmt.Sprintf("Server: %s", server))
	}
	if via := resp.Header.Get("Via"); via != "" {
		hops = append(hops, fmt.Sprintf("Via: %s", via))
	}
	if xForwardedFor := resp.Header.Get("X-Forwarded-For"); xForwardedFor != "" {
		hops = append(hops, fmt.Sprintf("X-Forwarded-For: %s", xForwardedFor))
	}

	// Add connection info
	if resp.TLS != nil {
		hops = append(hops, fmt.Sprintf("TLS Version: %s", getTLSVersion(resp.TLS.Version)))
		hops = append(hops, fmt.Sprintf("Cipher Suite: %s", getCipherSuite(resp.TLS.CipherSuite)))
	}

	result.Hops = hops
	result.RouteInfo = fmt.Sprintf("HTTP trace completed with %d hops", len(hops))

	return result, nil
}

// TestTCPTrace performs a TCP trace using traceroute-like functionality
func TestTCPTrace(req TCPTraceRequest) (*TraceResult, error) {
	result := &TraceResult{
		Target:   req.Target,
		Protocol: "tcp_trace",
	}

	// Default port to 22 (SSH) if not specified
	port := req.Port
	if port == 0 {
		port = 22
	}

	target := req.Target
	if !strings.Contains(target, ":") {
		target = fmt.Sprintf("%s:%d", target, port)
	}

	startTime := time.Now()

	// Try to resolve the target
	host, portStr, err := net.SplitHostPort(target)
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("Invalid target: %v", err)
		return result, err
	}

	ips, err := net.LookupIP(host)
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("DNS resolution failed: %v", err)
		return result, err
	}

	if len(ips) == 0 {
		result.Success = false
		result.Error = "No IP addresses found for target"
		return result, fmt.Errorf(result.Error)
	}

	targetIP := ips[0].String()

	// Use tcptraceroute if available, otherwise use traceroute with TCP
	var cmd *exec.Cmd
	if _, err := exec.LookPath("tcptraceroute"); err == nil {
		cmd = exec.Command("tcptraceroute", "-n", "-q", "1", "-w", "1", host, portStr)
	} else {
		// Fallback to traceroute with TCP (requires root on some systems)
		cmd = exec.Command("traceroute", "-T", "-n", "-q", "1", "-w", "1", "-p", portStr, host)
	}

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err = cmd.Run()

	result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0

	output := stdout.String()
	if output == "" {
		output = stderr.String()
	}

	// Parse traceroute output
	hops := parseTracerouteOutput(output)

	if len(hops) == 0 && err != nil {
		// If traceroute failed, try a simple TCP connection to show at least the final hop
		conn, dialErr := net.DialTimeout("tcp", target, 5*time.Second)
		if dialErr == nil {
			conn.Close()
			hops = append(hops, fmt.Sprintf("Direct connection to %s:%s successful", targetIP, portStr))
			result.Success = true
		} else {
			result.Success = false
			result.Error = fmt.Sprintf("Connection failed: %v", dialErr)
			return result, dialErr
		}
	} else {
		result.Success = true
	}

	result.Hops = hops
	result.RouteInfo = fmt.Sprintf("TCP trace to %s completed with %d hops", target, len(hops))

	return result, nil
}

// TestTraceroute performs an ICMP traceroute
func TestTraceroute(req TracerouteRequest) (*TraceResult, error) {
	result := &TraceResult{
		Target:   req.Target,
		Protocol: "traceroute",
	}

	timeout := req.Timeout
	if timeout == 0 {
		timeout = 30
	}

	startTime := time.Now()

	// Run traceroute command
	cmd := exec.Command("traceroute", "-n", "-q", "1", "-w", "2", "-m", "30", req.Target)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()

	result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0

	output := stdout.String()
	if output == "" {
		output = stderr.String()
	}

	// Parse traceroute output
	hops := parseTracerouteOutput(output)

	if len(hops) == 0 && err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("Traceroute failed: %v", err)
		if output != "" {
			result.Error += fmt.Sprintf(" - Output: %s", strings.TrimSpace(output))
		}
		return result, err
	}

	result.Success = true
	result.Hops = hops
	result.RouteInfo = fmt.Sprintf("Traceroute completed with %d hops", len(hops))

	return result, nil
}

// TestUDPTrace performs a UDP traceroute using traceroute with UDP mode
func TestUDPTrace(req UDPTraceRequest) (*TraceResult, error) {
	result := &TraceResult{
		Target:   req.Target,
		Protocol: "udp_trace",
	}

	// Default port to 53 (DNS) if not specified
	port := req.Port
	if port == 0 {
		port = 53
	}

	timeout := req.Timeout
	if timeout == 0 {
		timeout = 30
	}

	target := req.Target
	portStr := fmt.Sprintf("%d", port)

	startTime := time.Now()

	// Try to resolve the target
	ips, err := net.LookupIP(target)
	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("DNS resolution failed: %v", err)
		return result, err
	}

	if len(ips) == 0 {
		result.Success = false
		result.Error = "No IP addresses found for target"
		return result, fmt.Errorf(result.Error)
	}

	// Run traceroute in UDP mode (default mode for traceroute)
	// -n: numeric output (no DNS lookups)
	// -q 1: send only 1 query per hop
	// -w 2: wait 2 seconds for response
	// -m 30: max 30 hops
	// -p: port to use
	cmd := exec.Command("traceroute", "-n", "-q", "1", "-w", "2", "-m", "30", "-p", portStr, target)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err = cmd.Run()

	result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0

	output := stdout.String()
	if output == "" {
		output = stderr.String()
	}

	// Parse traceroute output
	hops := parseTracerouteOutput(output)

	if len(hops) == 0 && err != nil {
		// If traceroute failed, try a simple UDP connection to show at least the final hop
		conn, dialErr := net.DialTimeout("udp", fmt.Sprintf("%s:%d", target, port), 5*time.Second)
		if dialErr == nil {
			conn.Close()
			hops = append(hops, fmt.Sprintf("Direct UDP connection to %s:%d successful", ips[0].String(), port))
			result.Success = true
		} else {
			result.Success = false
			result.Error = fmt.Sprintf("UDP trace failed: %v", dialErr)
			if output != "" {
				result.Error += fmt.Sprintf(" - Output: %s", strings.TrimSpace(output))
			}
			return result, dialErr
		}
	} else {
		result.Success = true
	}

	result.Hops = hops
	result.RouteInfo = fmt.Sprintf("UDP trace to %s:%d completed with %d hops", target, port, len(hops))

	return result, nil
}

// parseTracerouteOutput parses traceroute command output into hop strings
func parseTracerouteOutput(output string) []string {
	var hops []string
	lines := strings.Split(output, "\n")

	// Regex to match traceroute lines
	hopRegex := regexp.MustCompile(`^\s*(\d+)\s+(.+)$`)

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "traceroute") {
			continue
		}

		matches := hopRegex.FindStringSubmatch(line)
		if len(matches) >= 3 {
			hopNum := matches[1]
			hopInfo := strings.TrimSpace(matches[2])

			// Clean up the hop info
			hopInfo = strings.ReplaceAll(hopInfo, "  ", " ")

			hops = append(hops, fmt.Sprintf("Hop %s: %s", hopNum, hopInfo))
		}
	}

	return hops
}

// Helper function to get TLS version string
func getTLSVersion(version uint16) string {
	switch version {
	case 0x0300:
		return "SSL 3.0"
	case 0x0301:
		return "TLS 1.0"
	case 0x0302:
		return "TLS 1.1"
	case 0x0303:
		return "TLS 1.2"
	case 0x0304:
		return "TLS 1.3"
	default:
		return fmt.Sprintf("Unknown (0x%04x)", version)
	}
}

// Helper function to get cipher suite name
func getCipherSuite(suite uint16) string {
	// Add common cipher suites
	suites := map[uint16]string{
		0x1301: "TLS_AES_128_GCM_SHA256",
		0x1302: "TLS_AES_256_GCM_SHA384",
		0x1303: "TLS_CHACHA20_POLY1305_SHA256",
		0xc02f: "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
		0xc030: "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
		0xcca8: "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
	}

	if name, ok := suites[suite]; ok {
		return name
	}
	return fmt.Sprintf("Unknown (0x%04x)", suite)
}

func (r *TraceResult) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}
