package handlers

import (
	"encoding/json"
	"net/http"
	"time"
)

type PingResponse struct {
	Timestamp  int64  `json:"timestamp"`
	ServerTime string `json:"server_time"`
	Latency    string `json:"latency"`
}

func PingHandler(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	response := PingResponse{
		Timestamp:  time.Now().UnixNano(),
		ServerTime: time.Now().UTC().Format(time.RFC3339Nano),
		Latency:    time.Since(startTime).String(),
	}

	json.NewEncoder(w).Encode(response)
}
