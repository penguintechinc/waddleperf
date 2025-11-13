package handlers

import (
	"encoding/json"
	"io"
	"net/http"
	"time"
)

type UploadResponse struct {
	BytesReceived int64   `json:"bytes_received"`
	Duration      float64 `json:"duration_seconds"`
	Throughput    float64 `json:"throughput_mbps"`
}

func UploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	startTime := time.Now()

	bytesReceived, err := io.Copy(io.Discard, r.Body)
	if err != nil {
		http.Error(w, "Error reading upload", http.StatusInternalServerError)
		return
	}
	defer r.Body.Close()

	duration := time.Since(startTime).Seconds()
	throughputMbps := float64(bytesReceived*8) / (duration * 1000000)

	response := UploadResponse{
		BytesReceived: bytesReceived,
		Duration:      duration,
		Throughput:    throughputMbps,
	}

	json.NewEncoder(w).Encode(response)
}
