package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/penguincloud/waddleperf/speedtest/internal/auth"
	"github.com/penguincloud/waddleperf/speedtest/internal/handlers"
	"github.com/penguincloud/waddleperf/speedtest/internal/middleware"
)

const (
	DefaultPort     = "5000"
	ReadTimeout     = 15 * time.Second
	WriteTimeout    = 60 * time.Second
	IdleTimeout     = 120 * time.Second
	ShutdownTimeout = 30 * time.Second
)

func main() {
	config := auth.LoadConfig()

	port := os.Getenv("PORT")
	if port == "" {
		port = DefaultPort
	}

	router := mux.NewRouter()

	authMiddleware := middleware.NewAuthMiddleware(config)

	router.HandleFunc("/health", handlers.HealthHandler).Methods("GET")

	api := router.PathPrefix("/").Subrouter()
	api.Use(authMiddleware.Authenticate)

	api.HandleFunc("/ping", handlers.PingHandler).Methods("GET")
	api.HandleFunc("/download", handlers.DownloadHandler).Methods("GET")
	api.HandleFunc("/upload", handlers.UploadHandler).Methods("POST")
	api.HandleFunc("/jitter", handlers.JitterHandler).Methods("GET")

	corsMiddleware := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	}

	router.Use(corsMiddleware)

	server := &http.Server{
		Addr:         fmt.Sprintf(":%s", port),
		Handler:      router,
		ReadTimeout:  ReadTimeout,
		WriteTimeout: WriteTimeout,
		IdleTimeout:  IdleTimeout,
	}

	go func() {
		log.Printf("WaddlePerf Speed Test Server starting on port %s", port)
		if config.EnableJWT {
			log.Println("JWT authentication: enabled")
		}
		if config.EnableBasicAuth {
			log.Println("Basic authentication: enabled")
		}
		if !config.EnableJWT && !config.EnableBasicAuth {
			log.Println("Authentication: disabled (anonymous mode)")
		}

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server gracefully...")

	ctx, cancel := context.WithTimeout(context.Background(), ShutdownTimeout)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("Server stopped")
}
