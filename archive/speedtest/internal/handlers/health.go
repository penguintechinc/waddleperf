package handlers

import (
	"encoding/json"
	"net/http"
	"time"
)

type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp int64  `json:"timestamp"`
	Version   string `json:"version"`
}

func HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-cache")

	response := HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Unix(),
		Version:   "1.0.0",
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}
