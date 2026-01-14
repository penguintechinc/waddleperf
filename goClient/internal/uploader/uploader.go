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
	TestID         string         `json:"test_id"`
	Name           string         `json:"name"`
	OrganizationID string         `json:"organization_id"`
	DeviceID       string         `json:"device_id"`
	Status         string         `json:"status"`
	DurationMS     int64          `json:"duration_ms"`
	Success        bool           `json:"success"`
	Metrics        map[string]interface{} `json:"metrics,omitempty"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
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
	jsonData, err := json.Marshal(result)
	if err != nil {
		return fmt.Errorf("failed to marshal result: %w", err)
	}

	url := fmt.Sprintf("%s/api/v1/tests/", u.managerURL)

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
	url := fmt.Sprintf("%s/health", u.managerURL)

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
