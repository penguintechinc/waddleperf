# Multi-stage build for goClient
# This Dockerfile is used by GitHub Actions for cross-platform builds

ARG TARGETOS
ARG TARGETARCH

FROM golang:1.23-bookworm AS builder

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build for target platform
ARG TARGETOS
ARG TARGETARCH
ARG VERSION=dev
ARG BUILD_TIME
ARG GIT_COMMIT

RUN GOOS=${TARGETOS} GOARCH=${TARGETARCH} CGO_ENABLED=0 go build \
    -ldflags="-w -s -X main.Version=${VERSION} -X main.BuildTime=${BUILD_TIME} -X main.GitCommit=${GIT_COMMIT}" \
    -o waddleperf \
    ./cmd/waddleperf

# Create minimal runtime image
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    iputils \
    bind-tools \
    traceroute

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/waddleperf /app/waddleperf

# Create config directory
RUN mkdir -p /app/config

# Run as non-root user
RUN adduser -D -u 1000 waddleperf && \
    chown -R waddleperf:waddleperf /app
USER waddleperf

ENTRYPOINT ["/app/waddleperf"]
CMD ["daemon"]
