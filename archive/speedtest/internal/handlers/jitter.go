package handlers

import (
	"encoding/json"
	"math"
	"net/http"
	"strconv"
	"time"
)

type JitterResponse struct {
	Samples        int     `json:"samples"`
	AverageLatency float64 `json:"average_latency_ms"`
	MinLatency     float64 `json:"min_latency_ms"`
	MaxLatency     float64 `json:"max_latency_ms"`
	Jitter         float64 `json:"jitter_ms"`
	StdDev         float64 `json:"std_dev_ms"`
	Timestamps     []int64 `json:"timestamps"`
}

func JitterHandler(w http.ResponseWriter, r *http.Request) {
	samplesStr := r.URL.Query().Get("samples")
	samples := 10

	if samplesStr != "" {
		if s, err := strconv.Atoi(samplesStr); err == nil && s > 0 && s <= 100 {
			samples = s
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	latencies := make([]float64, samples)
	timestamps := make([]int64, samples)

	for i := 0; i < samples; i++ {
		start := time.Now()
		time.Sleep(time.Millisecond)
		latency := float64(time.Since(start).Microseconds()) / 1000.0
		latencies[i] = latency
		timestamps[i] = time.Now().UnixNano()
	}

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

	avg := sum / float64(samples)

	var varianceSum float64
	var jitterSum float64
	for i, lat := range latencies {
		varianceSum += math.Pow(lat-avg, 2)
		if i > 0 {
			jitterSum += math.Abs(lat - latencies[i-1])
		}
	}

	stdDev := math.Sqrt(varianceSum / float64(samples))
	jitter := jitterSum / float64(samples-1)

	response := JitterResponse{
		Samples:        samples,
		AverageLatency: avg,
		MinLatency:     min,
		MaxLatency:     max,
		Jitter:         jitter,
		StdDev:         stdDev,
		Timestamps:     timestamps,
	}

	json.NewEncoder(w).Encode(response)
}
