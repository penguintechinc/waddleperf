package scheduler

import (
	"context"
	"fmt"
	"log"
	"net"
	"sync"
	"time"

	"github.com/penguintechinc/WaddlePerf/goClient/internal/config"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/device"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/protocols"
	"github.com/penguintechinc/WaddlePerf/goClient/internal/uploader"
)

type Scheduler struct {
	config       *config.Config
	uploader     *uploader.Uploader
	deviceInfo   *device.DeviceInfo
	ticker       *time.Ticker
	stopChan     chan struct{}
	isRunning    bool
	mu           sync.Mutex
	lastRunTime  time.Time
	successCount int
	failureCount int
}

func NewScheduler(cfg *config.Config, upl *uploader.Uploader, devInfo *device.DeviceInfo) *Scheduler {
	return &Scheduler{
		config:     cfg,
		uploader:   upl,
		deviceInfo: devInfo,
		stopChan:   make(chan struct{}),
	}
}

func (s *Scheduler) Start(ctx context.Context) error {
	s.mu.Lock()
	if s.isRunning {
		s.mu.Unlock()
		return fmt.Errorf("scheduler is already running")
	}
	s.isRunning = true
	s.mu.Unlock()

	// Run on startup if configured
	if s.config.Schedule.RunOnStartup {
		log.Println("Running tests on startup...")
		s.RunTests()
	}

	// Start periodic execution
	interval := time.Duration(s.config.Schedule.IntervalSeconds) * time.Second
	s.ticker = time.NewTicker(interval)

	log.Printf("Scheduler started with interval: %v", interval)

	go func() {
		for {
			select {
			case <-s.ticker.C:
				log.Println("Running scheduled tests...")
				s.RunTests()
			case <-s.stopChan:
				s.ticker.Stop()
				log.Println("Scheduler stopped")
				return
			case <-ctx.Done():
				s.ticker.Stop()
				log.Println("Scheduler stopped (context cancelled)")
				return
			}
		}
	}()

	return nil
}

func (s *Scheduler) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.isRunning {
		return
	}

	close(s.stopChan)
	s.isRunning = false
}

func (s *Scheduler) RunTests() error {
	s.mu.Lock()
	s.lastRunTime = time.Now()
	s.mu.Unlock()

	var wg sync.WaitGroup
	results := make([]*uploader.TestResultUpload, 0)
	resultsMu := sync.Mutex{}

	// Run HTTP tests
	if s.config.Tests.HTTP.Enabled {
		for _, target := range s.config.Tests.HTTP.Targets {
			wg.Add(1)
			go func(tgt string) {
				defer wg.Done()
				result := s.runHTTPTest(tgt)
				if result != nil {
					resultsMu.Lock()
					results = append(results, result)
					resultsMu.Unlock()
				}
			}(target)
		}
	}

	// Run TCP tests
	if s.config.Tests.TCP.Enabled {
		for _, target := range s.config.Tests.TCP.Targets {
			wg.Add(1)
			go func(tgt config.TCPTargetConfig) {
				defer wg.Done()
				result := s.runTCPTest(tgt)
				if result != nil {
					resultsMu.Lock()
					results = append(results, result)
					resultsMu.Unlock()
				}
			}(target)
		}
	}

	// Run UDP tests
	if s.config.Tests.UDP.Enabled {
		for _, target := range s.config.Tests.UDP.Targets {
			wg.Add(1)
			go func(tgt config.UDPTargetConfig) {
				defer wg.Done()
				result := s.runUDPTest(tgt)
				if result != nil {
					resultsMu.Lock()
					results = append(results, result)
					resultsMu.Unlock()
				}
			}(target)
		}
	}

	// Run ICMP tests
	if s.config.Tests.ICMP.Enabled {
		for _, target := range s.config.Tests.ICMP.Targets {
			wg.Add(1)
			go func(tgt string) {
				defer wg.Done()
				result := s.runICMPTest(tgt)
				if result != nil {
					resultsMu.Lock()
					results = append(results, result)
					resultsMu.Unlock()
				}
			}(target)
		}
	}

	// Wait for all tests to complete
	wg.Wait()

	// Upload results
	log.Printf("Tests completed. Uploading %d results...", len(results))
	for _, result := range results {
		if err := s.uploader.UploadResult(result); err != nil {
			log.Printf("Failed to upload result for %s: %v", result.Target, err)
			s.mu.Lock()
			s.failureCount++
			s.mu.Unlock()
		} else {
			log.Printf("Successfully uploaded result for %s", result.Target)
			s.mu.Lock()
			s.successCount++
			s.mu.Unlock()
		}
	}

	return nil
}

func (s *Scheduler) runHTTPTest(target string) *uploader.TestResultUpload {
	req := protocols.HTTPTestRequest{
		Target:   target,
		Protocol: s.config.Tests.HTTP.Protocol,
		Method:   s.config.Tests.HTTP.Advanced.Method,
		Timeout:  s.config.Tests.HTTP.Timeout,
	}

	result, err := protocols.TestHTTP(req)
	if err != nil {
		log.Printf("HTTP test failed for %s: %v", target, err)
		return &uploader.TestResultUpload{
			DeviceInfo:     s.deviceInfo,
			TestType:       "http",
			ProtocolDetail: req.Protocol,
			Target:         target,
			Success:        false,
			RawResults:     map[string]string{"error": err.Error()},
			Timestamp:      time.Now(),
		}
	}

	return &uploader.TestResultUpload{
		DeviceInfo:     s.deviceInfo,
		TestType:       "http",
		ProtocolDetail: result.ConnectedProto,
		Target:         target,
		TargetIP:       resolveHostname(target),
		LatencyMS:      result.LatencyMS,
		ThroughputMBps: result.TransferSpeedMBs,
		Success:        result.Success,
		RawResults:     result,
		Timestamp:      time.Now(),
	}
}

func (s *Scheduler) runTCPTest(target config.TCPTargetConfig) *uploader.TestResultUpload {
	req := protocols.TCPTestRequest{
		Target:   target.Address,
		Protocol: target.Protocol,
		Timeout:  s.config.Tests.TCP.Timeout,
	}

	result, err := protocols.TestTCP(req)
	if err != nil {
		log.Printf("TCP test failed for %s: %v", target.Address, err)
		return &uploader.TestResultUpload{
			DeviceInfo:     s.deviceInfo,
			TestType:       "tcp",
			ProtocolDetail: target.Protocol,
			Target:         target.Address,
			Success:        false,
			RawResults:     map[string]string{"error": err.Error()},
			Timestamp:      time.Now(),
		}
	}

	return &uploader.TestResultUpload{
		DeviceInfo:     s.deviceInfo,
		TestType:       "tcp",
		ProtocolDetail: target.Protocol,
		Target:         target.Address,
		TargetIP:       resolveHostname(target.Address),
		LatencyMS:      result.LatencyMS,
		Success:        result.Success,
		RawResults:     result,
		Timestamp:      time.Now(),
	}
}

func (s *Scheduler) runUDPTest(target config.UDPTargetConfig) *uploader.TestResultUpload {
	req := protocols.UDPTestRequest{
		Target:   target.Address,
		Protocol: target.Protocol,
		Timeout:  s.config.Tests.UDP.Timeout,
		Query:    target.Query,
	}

	result, err := protocols.TestUDP(req)
	if err != nil {
		log.Printf("UDP test failed for %s: %v", target.Address, err)
		return &uploader.TestResultUpload{
			DeviceInfo:     s.deviceInfo,
			TestType:       "udp",
			ProtocolDetail: target.Protocol,
			Target:         target.Address,
			Success:        false,
			RawResults:     map[string]string{"error": err.Error()},
			Timestamp:      time.Now(),
		}
	}

	return &uploader.TestResultUpload{
		DeviceInfo:     s.deviceInfo,
		TestType:       "udp",
		ProtocolDetail: target.Protocol,
		Target:         target.Address,
		TargetIP:       resolveHostname(target.Address),
		LatencyMS:      result.LatencyMS,
		Success:        result.Success,
		RawResults:     result,
		Timestamp:      time.Now(),
	}
}

func (s *Scheduler) runICMPTest(target string) *uploader.TestResultUpload {
	req := protocols.ICMPTestRequest{
		Target:   target,
		Protocol: s.config.Tests.ICMP.Protocol,
		Count:    s.config.Tests.ICMP.Count,
		Timeout:  s.config.Tests.ICMP.Timeout,
	}

	result, err := protocols.TestICMP(req)
	if err != nil {
		log.Printf("ICMP test failed for %s: %v", target, err)
		return &uploader.TestResultUpload{
			DeviceInfo:     s.deviceInfo,
			TestType:       "icmp",
			ProtocolDetail: req.Protocol,
			Target:         target,
			Success:        false,
			RawResults:     map[string]string{"error": err.Error()},
			Timestamp:      time.Now(),
		}
	}

	packetLoss := 0.0
	if result.PacketsSent > 0 {
		packetLoss = float64(result.PacketsSent-result.PacketsReceived) / float64(result.PacketsSent) * 100.0
	}

	return &uploader.TestResultUpload{
		DeviceInfo:        s.deviceInfo,
		TestType:          "icmp",
		ProtocolDetail:    req.Protocol,
		Target:            target,
		TargetIP:          resolveHostname(target),
		LatencyMS:         result.LatencyMS,
		JitterMS:          result.JitterMS,
		PacketLossPercent: packetLoss,
		Success:           result.Success,
		RawResults:        result,
		Timestamp:         time.Now(),
	}
}

func (s *Scheduler) GetStats() map[string]interface{} {
	s.mu.Lock()
	defer s.mu.Unlock()

	return map[string]interface{}{
		"is_running":       s.isRunning,
		"last_run_time":    s.lastRunTime,
		"success_count":    s.successCount,
		"failure_count":    s.failureCount,
		"interval_seconds": s.config.Schedule.IntervalSeconds,
	}
}

func resolveHostname(hostport string) string {
	host, _, err := net.SplitHostPort(hostport)
	if err != nil {
		// If no port, use as-is
		host = hostport
	}

	// Check if it's already an IP
	if net.ParseIP(host) != nil {
		return host
	}

	// Resolve hostname
	ips, err := net.LookupIP(host)
	if err != nil || len(ips) == 0 {
		return "unknown"
	}

	return ips[0].String()
}
