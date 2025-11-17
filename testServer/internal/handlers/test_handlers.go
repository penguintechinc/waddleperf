package handlers

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/penguincloud/waddleperf/testserver/internal/auth"
	"github.com/penguincloud/waddleperf/testserver/internal/database"
	"github.com/penguincloud/waddleperf/testserver/internal/protocols"
)

type TestHandlers struct {
	db *database.DB
}

func New(db *database.DB) *TestHandlers {
	return &TestHandlers{db: db}
}

func (h *TestHandlers) HTTPTestHandler(w http.ResponseWriter, r *http.Request) {
	var req protocols.HTTPTestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := protocols.TestHTTP(req)
	if err != nil {
		log.Printf("HTTP test failed: %v", err)
		http.Error(w, "Test execution failed", http.StatusInternalServerError)
		return
	}

	if err := h.saveTestResult(r, "http", req.Protocol, req.Target, result); err != nil {
		log.Printf("Failed to save test result: %v", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *TestHandlers) TCPTestHandler(w http.ResponseWriter, r *http.Request) {
	var req protocols.TCPTestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := protocols.TestTCP(req)
	if err != nil {
		log.Printf("TCP test failed: %v", err)
		http.Error(w, "Test execution failed", http.StatusInternalServerError)
		return
	}

	if err := h.saveTestResult(r, "tcp", req.Protocol, req.Target, result); err != nil {
		log.Printf("Failed to save test result: %v", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *TestHandlers) UDPTestHandler(w http.ResponseWriter, r *http.Request) {
	var req protocols.UDPTestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := protocols.TestUDP(req)
	if err != nil {
		log.Printf("UDP test failed: %v", err)
		http.Error(w, "Test execution failed", http.StatusInternalServerError)
		return
	}

	if err := h.saveTestResult(r, "udp", req.Protocol, req.Target, result); err != nil {
		log.Printf("Failed to save test result: %v", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *TestHandlers) ICMPTestHandler(w http.ResponseWriter, r *http.Request) {
	var req protocols.ICMPTestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := protocols.TestICMP(req)
	if err != nil {
		log.Printf("ICMP test failed: %v", err)
		http.Error(w, "Test execution failed", http.StatusInternalServerError)
		return
	}

	if err := h.saveTestResult(r, "icmp", req.Protocol, req.Target, result); err != nil {
		log.Printf("Failed to save test result: %v", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *TestHandlers) HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"version": "1.0.0",
	})
}

func (h *TestHandlers) saveTestResult(r *http.Request, testType, protocolDetail, targetHost string, resultData interface{}) error {
	user := auth.GetUser(r.Context())

	// Get device info from headers
	deviceSerial := r.Header.Get("X-Device-Serial")
	if deviceSerial == "" {
		deviceSerial = "unknown"
	}
	deviceHostname := r.Header.Get("X-Device-Hostname")
	if deviceHostname == "" {
		deviceHostname = "unknown"
	}
	deviceOS := r.Header.Get("X-Device-OS")
	if deviceOS == "" {
		deviceOS = "unknown"
	}
	deviceOSVersion := r.Header.Get("X-Device-OS-Version")
	if deviceOSVersion == "" {
		deviceOSVersion = "unknown"
	}

	// Get client IP
	clientIP := r.RemoteAddr
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		clientIP = forwarded
	}

	// Extract metrics from result
	var latency, throughput, jitter, packetLoss *float64
	targetIP := targetHost
	rawResults := make(map[string]interface{})

	switch v := resultData.(type) {
	case *protocols.HTTPTestResult:
		latency = &v.LatencyMS
		rawResults["status_code"] = v.StatusCode
		rawResults["ttfb_ms"] = v.TTFBMS
		rawResults["total_time_ms"] = v.TotalTimeMS
	case *protocols.TCPTestResult:
		latency = &v.LatencyMS
		if v.HandshakeMS > 0 {
			rawResults["handshake_ms"] = v.HandshakeMS
		}
		targetIP = v.RemoteAddr
	case *protocols.UDPTestResult:
		latency = &v.LatencyMS
		targetIP = v.RemoteAddr
	case *protocols.ICMPTestResult:
		latency = &v.LatencyMS
		jitter = &v.JitterMS
		packetLoss = &v.PacketLossPercent
		rawResults["packets_sent"] = v.PacketsSent
		rawResults["packets_received"] = v.PacketsReceived
	}

	testResult := &database.TestResult{
		DeviceSerial:      deviceSerial,
		DeviceHostname:    deviceHostname,
		DeviceOS:          deviceOS,
		DeviceOSVersion:   deviceOSVersion,
		TestType:          testType,
		ProtocolDetail:    protocolDetail,
		TargetHost:        targetHost,
		TargetIP:          targetIP,
		ClientIP:          clientIP,
		LatencyMS:         latency,
		ThroughputMbps:    throughput,
		JitterMS:          jitter,
		PacketLossPercent: packetLoss,
		RawResults:        rawResults,
	}

	if user != nil {
		testResult.UserID = &user.ID
	}

	_, err := h.db.InsertTestResult(testResult)
	return err
}
