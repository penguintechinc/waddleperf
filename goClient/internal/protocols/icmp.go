package protocols

import (
	"encoding/json"
	"fmt"
	"math"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"time"
)

type ICMPTestRequest struct {
	Target   string `json:"target"`
	Protocol string `json:"protocol"` // ping, traceroute
	Count    int    `json:"count"`
	Timeout  int    `json:"timeout"`
}

type ICMPTestResult struct {
	Target            string   `json:"target"`
	Protocol          string   `json:"protocol"`
	Success           bool     `json:"success"`
	PacketsSent       int      `json:"packets_sent"`
	PacketsReceived   int      `json:"packets_received"`
	PacketLossPercent float64  `json:"packet_loss_percent"`
	LatencyMS         float64  `json:"latency_ms"` // Average
	MinLatencyMS      float64  `json:"min_latency_ms"`
	MaxLatencyMS      float64  `json:"max_latency_ms"`
	JitterMS          float64  `json:"jitter_ms"`
	StdDevMS          float64  `json:"stddev_ms"`
	Error             string   `json:"error,omitempty"`
	Hops              []string `json:"hops,omitempty"` // For traceroute
	TotalTimeMS       float64  `json:"total_time_ms"`
}

func TestICMP(req ICMPTestRequest) (*ICMPTestResult, error) {
	result := &ICMPTestResult{
		Target:   req.Target,
		Protocol: req.Protocol,
	}

	if req.Count == 0 {
		req.Count = 4
	}
	if req.Timeout == 0 {
		req.Timeout = 10
	}

	switch req.Protocol {
	case "ping":
		return testPing(req.Target, req.Count, req.Timeout, result)
	case "traceroute":
		return testTraceroute(req.Target, req.Timeout, result)
	default:
		result.Error = fmt.Sprintf("unsupported protocol: %s", req.Protocol)
		return result, fmt.Errorf(result.Error)
	}
}

func testPing(target string, count, timeout int, result *ICMPTestResult) (*ICMPTestResult, error) {
	startTime := time.Now()

	var cmd *exec.Cmd

	switch runtime.GOOS {
	case "linux":
		cmd = exec.Command("ping", "-c", strconv.Itoa(count), "-W", strconv.Itoa(timeout), target)
	case "darwin":
		cmd = exec.Command("ping", "-c", strconv.Itoa(count), "-W", strconv.Itoa(timeout*1000), target)
	case "windows":
		cmd = exec.Command("ping", "-n", strconv.Itoa(count), "-w", strconv.Itoa(timeout*1000), target)
	default:
		result.Error = "unsupported platform for ping"
		return result, fmt.Errorf(result.Error)
	}

	output, err := cmd.CombinedOutput()
	totalTime := time.Since(startTime)
	result.TotalTimeMS = float64(totalTime.Microseconds()) / 1000.0

	if err != nil {
		result.Success = false
		result.Error = fmt.Sprintf("ping command failed: %v", err)
		return result, err
	}

	// Parse ping output
	lines := strings.Split(string(output), "\n")
	latencies := []float64{}

	for _, line := range lines {
		// Parse different formats
		if strings.Contains(line, "time=") {
			// Linux/Mac format: "time=12.3 ms" or "time=12.3ms"
			parts := strings.Split(line, "time=")
			if len(parts) > 1 {
				timeStr := strings.TrimSpace(parts[1])
				timeStr = strings.TrimSuffix(timeStr, "ms")
				timeStr = strings.TrimSuffix(timeStr, " ms")
				timeStr = strings.Fields(timeStr)[0]
				if latency, err := strconv.ParseFloat(timeStr, 64); err == nil {
					latencies = append(latencies, latency)
				}
			}
		} else if strings.Contains(line, "Time=") {
			// Windows format: "Time=12ms" or "Time=12 ms"
			parts := strings.Split(line, "Time=")
			if len(parts) > 1 {
				timeStr := strings.TrimSpace(parts[1])
				timeStr = strings.TrimSuffix(timeStr, "ms")
				timeStr = strings.TrimSuffix(timeStr, " ms")
				timeStr = strings.Fields(timeStr)[0]
				if latency, err := strconv.ParseFloat(timeStr, 64); err == nil {
					latencies = append(latencies, latency)
				}
			}
		}
	}

	result.PacketsSent = count
	result.PacketsReceived = len(latencies)

	if count > 0 {
		result.PacketLossPercent = float64(count-len(latencies)) / float64(count) * 100.0
	}

	if len(latencies) > 0 {
		result.Success = true

		// Calculate stats
		var sum, min, max float64
		min = latencies[0]
		max = latencies[0]

		for _, lat := range latencies {
			sum += lat
			if lat < min {
				min = lat
			}
			if lat > max {
				max = lat
			}
		}

		result.LatencyMS = sum / float64(len(latencies))
		result.MinLatencyMS = min
		result.MaxLatencyMS = max

		// Calculate jitter (average consecutive difference)
		var jitterSum float64
		for i := 1; i < len(latencies); i++ {
			jitterSum += math.Abs(latencies[i] - latencies[i-1])
		}
		if len(latencies) > 1 {
			result.JitterMS = jitterSum / float64(len(latencies)-1)
		}

		// Calculate standard deviation
		var varianceSum float64
		for _, lat := range latencies {
			diff := lat - result.LatencyMS
			varianceSum += diff * diff
		}
		if len(latencies) > 1 {
			result.StdDevMS = math.Sqrt(varianceSum / float64(len(latencies)))
		}
	} else {
		result.Success = false
		result.Error = "No packets received"
	}

	return result, nil
}

func testTraceroute(target string, timeout int, result *ICMPTestResult) (*ICMPTestResult, error) {
	startTime := time.Now()

	var cmd *exec.Cmd

	switch runtime.GOOS {
	case "linux":
		cmd = exec.Command("traceroute", "-w", strconv.Itoa(timeout), "-m", "30", target)
	case "darwin":
		cmd = exec.Command("traceroute", "-w", strconv.Itoa(timeout), "-m", "30", target)
	case "windows":
		cmd = exec.Command("tracert", "-w", strconv.Itoa(timeout*1000), "-h", "30", target)
	default:
		result.Error = "unsupported platform for traceroute"
		return result, fmt.Errorf(result.Error)
	}

	output, err := cmd.CombinedOutput()
	totalTime := time.Since(startTime)
	result.TotalTimeMS = float64(totalTime.Microseconds()) / 1000.0

	if err != nil {
		// Traceroute may return error but still have useful output
		result.Success = false
		result.Error = fmt.Sprintf("traceroute completed with errors: %v", err)
	} else {
		result.Success = true
	}

	// Parse traceroute output
	lines := strings.Split(string(output), "\n")
	hops := []string{}

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "traceroute") || strings.HasPrefix(line, "Tracing") {
			continue
		}
		hops = append(hops, line)
	}

	result.Hops = hops
	if len(hops) > 0 {
		result.Success = true
	}

	return result, nil
}

func (r *ICMPTestResult) ToJSON() ([]byte, error) {
	return json.Marshal(r)
}
