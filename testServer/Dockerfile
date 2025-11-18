# Build stage
FROM golang:1.23-bookworm AS builder

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary for target architecture
ARG TARGETOS=linux
ARG TARGETARCH=amd64
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a \
    -o testserver \
    ./cmd/testserver

# Runtime stage
FROM alpine:3.19

# Install runtime dependencies (for ping, traceroute, etc.)
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    iputils \
    bind-tools \
    traceroute \
    tcptraceroute \
    libcap \
    openssh-client && \
    addgroup -g 1000 waddleperf && \
    adduser -D -u 1000 -G waddleperf waddleperf && \
    setcap cap_net_raw+ep /usr/bin/traceroute && \
    setcap cap_net_raw+ep /usr/bin/tcptraceroute

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/testserver /app/testserver

# Set ownership
RUN chown -R waddleperf:waddleperf /app

# Switch to non-root user
USER waddleperf

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Set environment defaults
ENV PORT=8080 \
    LOG_LEVEL=info \
    AUTH_ENABLED=true \
    MAX_CONCURRENT_TESTS=100

# Run
CMD ["/app/testserver"]
