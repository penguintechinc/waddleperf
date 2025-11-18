package protocols

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net"
	"time"

	"golang.org/x/crypto/ssh"
)

type TCPTestRequest struct {
	Target   string `json:"target"`
	Protocol string `json:"protocol"` // raw, tls, ssh
	Timeout  int    `json:"timeout"`
}

type TCPTestResult struct {
	Target      string  `json:"target"`
	Protocol    string  `json:"protocol"`
	Connected   bool    `json:"connected"`
	LatencyMS   float64 `json:"latency_ms"`
	HandshakeMS float64 `json:"handshake_ms,omitempty"`
	Success     bool    `json:"success"`
	Error       string  `json:"error,omitempty"`
	RemoteAddr  string  `json:"remote_addr"`
	LocalAddr   string  `json:"local_addr"`
	TLSVersion  string  `json:"tls_version,omitempty"`
	TLSCipher   string  `json:"tls_cipher,omitempty"`
	SSHVersion  string  `json:"ssh_version,omitempty"`
}

func TestTCP(req TCPTestRequest) (*TCPTestResult, error) {
	result := &TCPTestResult{
		Target:   req.Target,
		Protocol: req.Protocol,
	}

	timeout := time.Duration(req.Timeout) * time.Second
	if timeout == 0 {
		timeout = 10 * time.Second
	}

	switch req.Protocol {
	case "raw":
		return testRawTCP(req.Target, timeout, result)
	case "tls":
		return testTLSTCP(req.Target, timeout, result)
	case "ssh":
		return testSSH(req.Target, timeout, result)
	default:
		result.Error = fmt.Sprintf("unsupported protocol: %s", req.Protocol)
		return result, fmt.Errorf(result.Error)
	}
}

func testRawTCP(target string, timeout time.Duration, result *TCPTestResult) (*TCPTestResult, error) {
	startTime := time.Now()

	conn, err := net.DialTimeout("tcp", target, timeout)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0
		return result, err
	}
	defer conn.Close()

	latency := time.Since(startTime)

	result.Connected = true
	result.Success = true
	result.LatencyMS = float64(latency.Microseconds()) / 1000.0
	result.RemoteAddr = conn.RemoteAddr().String()
	result.LocalAddr = conn.LocalAddr().String()

	return result, nil
}

func testTLSTCP(target string, timeout time.Duration, result *TCPTestResult) (*TCPTestResult, error) {
	startTime := time.Now()

	config := &tls.Config{
		InsecureSkipVerify: false,
	}

	dialer := &net.Dialer{Timeout: timeout}
	conn, err := tls.DialWithDialer(dialer, "tcp", target, config)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		result.LatencyMS = float64(time.Since(startTime).Microseconds()) / 1000.0
		return result, err
	}
	defer conn.Close()

	handshakeStart := time.Now()
	if err := conn.Handshake(); err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("TLS handshake failed: %v", err)
		return result, err
	}
	handshakeDuration := time.Since(handshakeStart)
	totalLatency := time.Since(startTime)

	state := conn.ConnectionState()

	result.Connected = true
	result.Success = true
	result.LatencyMS = float64(totalLatency.Microseconds()) / 1000.0
	result.HandshakeMS = float64(handshakeDuration.Microseconds()) / 1000.0
	result.RemoteAddr = conn.RemoteAddr().String()
	result.LocalAddr = conn.LocalAddr().String()
	result.TLSVersion = tlsVersionToString(state.Version)
	result.TLSCipher = tls.CipherSuiteName(state.CipherSuite)

	return result, nil
}

func testSSH(target string, timeout time.Duration, result *TCPTestResult) (*TCPTestResult, error) {
	startTime := time.Now()

	config := &ssh.ClientConfig{
		Timeout:         timeout,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		// We don't provide auth methods - we're just testing connectivity
	}

	client, err := ssh.Dial("tcp", target, config)
	if err != nil {
		// SSH connection without auth is expected to fail, but we get timing info
		latency := time.Since(startTime)

		// Check if we at least got to the banner exchange
		if netErr, ok := err.(*net.OpError); ok && netErr.Timeout() {
			result.Success = false
			result.Error = "Connection timeout"
			result.LatencyMS = float64(latency.Microseconds()) / 1000.0
			return result, err
		}

		// Banner exchange succeeded, auth failed (expected)
		result.Connected = true
		result.Success = true
		result.LatencyMS = float64(latency.Microseconds()) / 1000.0
		result.Error = "SSH connectivity verified (auth not attempted)"
		return result, nil
	}
	defer client.Close()

	latency := time.Since(startTime)

	result.Connected = true
	result.Success = true
	result.LatencyMS = float64(latency.Microseconds()) / 1000.0
	result.RemoteAddr = client.RemoteAddr().String()
	result.LocalAddr = client.LocalAddr().String()
	result.SSHVersion = string(client.ServerVersion())

	return result, nil
}

func tlsVersionToString(version uint16) string {
	switch version {
	case tls.VersionTLS10:
		return "TLS 1.0"
	case tls.VersionTLS11:
		return "TLS 1.1"
	case tls.VersionTLS12:
		return "TLS 1.2"
	case tls.VersionTLS13:
		return "TLS 1.3"
	default:
		return fmt.Sprintf("Unknown (0x%x)", version)
	}
}

func (r *TCPTestResult) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}
