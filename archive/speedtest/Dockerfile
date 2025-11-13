# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /build

RUN apk add --no-cache git ca-certificates tzdata

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a \
    -o speedtest \
    ./cmd/speedtest

# Runtime stage
FROM alpine:3.19

RUN apk add --no-cache ca-certificates tzdata && \
    addgroup -g 1000 speedtest && \
    adduser -D -u 1000 -G speedtest speedtest

WORKDIR /app

COPY --from=builder /build/speedtest /app/speedtest

RUN chown -R speedtest:speedtest /app

USER speedtest

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

ENV PORT=5000

CMD ["/app/speedtest"]
