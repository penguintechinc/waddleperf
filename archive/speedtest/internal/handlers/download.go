package handlers

import (
	"crypto/rand"
	"net/http"
	"strconv"
)

const (
	DefaultChunkSize = 1024 * 1024        // 1MB chunks
	DefaultTotalSize = 100 * 1024 * 1024  // 100MB default
	MaxTotalSize     = 1024 * 1024 * 1024 // 1GB max
)

var randomData []byte

func init() {
	randomData = make([]byte, DefaultChunkSize)
	rand.Read(randomData)
}

func DownloadHandler(w http.ResponseWriter, r *http.Request) {
	sizeStr := r.URL.Query().Get("size")
	totalSize := int64(DefaultTotalSize)

	if sizeStr != "" {
		if size, err := strconv.ParseInt(sizeStr, 10, 64); err == nil {
			if size > 0 && size <= MaxTotalSize {
				totalSize = size
			}
		}
	}

	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Length", strconv.FormatInt(totalSize, 10))
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	var written int64
	chunkSize := int64(len(randomData))

	for written < totalSize {
		remaining := totalSize - written
		toWrite := chunkSize
		if remaining < chunkSize {
			toWrite = remaining
		}

		n, err := w.Write(randomData[:toWrite])
		if err != nil {
			return
		}

		written += int64(n)

		if f, ok := w.(http.Flusher); ok {
			f.Flush()
		}
	}
}
