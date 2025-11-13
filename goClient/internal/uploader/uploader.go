package uploader

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/penguintechinc/WaddlePerf/goClient/internal/device"
)

type TestResultUpload struct {
	DeviceInfo        *device.DeviceInfo `json:"device_info"`
	TestType          string             `json:"test_type"`
	ProtocolDetail    string             `json:"protocol_detail"`
	Target            string             `json:"target"`
	TargetIP          string             `json:"target_ip,omitempty"`
	LatencyMS         float64            `json:"latency_ms"`
	ThroughputMBps    float64            `json:"throughput_mbps,omitempty"`
	JitterMS          float64            `json:"jitter_ms,omitempty"`
	PacketLossPercent float64            `json:"packet_loss_percent,omitempty"`
	Success           bool               `json:"success"`
	RawResults        interface{}        `json:"raw_results"`
	Timestamp         time.Time          `json:"timestamp"`
}

type Uploader struct {
	managerURL string
	apiKey     string
	httpClient *http.Client
}

func NewUploader(managerURL, apiKey string) *Uploader {
	return &Uploader{
		managerURL: managerURL,
		apiKey:     apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (u *Uploader) UploadResult(result *TestResultUpload) error {
	if result.Timestamp.IsZero() {
		result.Timestamp = time.Now()
	}

	jsonData, err := json.Marshal(result)
	if err != nil {
		return fmt.Errorf("failed to marshal result: %w", err)
	}

	url := fmt.Sprintf("%s/api/v1/results/upload", u.managerURL)

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", u.apiKey))
	req.Header.Set("User-Agent", "WaddlePerf-GoClient/1.0")

	resp, err := u.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to upload result: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("upload failed with status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

func (u *Uploader) UploadBatch(results []*TestResultUpload) error {
	for _, result := range results {
		if err := u.UploadResult(result); err != nil {
			return err
		}
	}
	return nil
}

func (u *Uploader) TestConnection() error {
	url := fmt.Sprintf("%s/api/v1/health", u.managerURL)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", u.apiKey))

	resp, err := u.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to connect to manager: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("health check failed with status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}
