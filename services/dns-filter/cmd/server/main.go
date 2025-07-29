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

	"guardnet/dns-filter/internal/config"
	"guardnet/dns-filter/internal/dns"
	"guardnet/dns-filter/internal/db"
	"guardnet/dns-filter/internal/cache"
	"guardnet/dns-filter/internal/metrics"
	"guardnet/dns-filter/pkg/logger"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	// Initialize logger
	log := logger.New()
	log.Info("Starting GuardNet DNS Filter Service")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatal("Failed to load configuration", "error", err)
	}

	// Initialize database connection
	database, err := db.NewConnection(cfg.DatabaseURL)
	if err != nil {
		log.Fatal("Failed to connect to database", "error", err)
	}
	defer database.Close()

	// Initialize Redis cache
	redisClient, err := cache.NewRedisClient(cfg.RedisURL)
	if err != nil {
		log.Fatal("Failed to connect to Redis", "error", err)
	}
	defer redisClient.Close()

	// Initialize metrics
	metricsCollector := metrics.NewCollector()

	// Create DNS server
	dnsServer := dns.NewServer(&dns.Config{
		Address:    cfg.DNSAddress,
		Database:   database,
		Cache:      redisClient,
		Metrics:    metricsCollector,
		Logger:     log,
	})

	// Start DNS server in goroutine
	go func() {
		log.Info("Starting DNS server", "address", cfg.DNSAddress)
		if err := dnsServer.Start(); err != nil {
			log.Fatal("DNS server failed to start", "error", err)
		}
	}()

	// Setup HTTP server for health checks and metrics
	router := mux.NewRouter()
	
	// Health check endpoint
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"healthy","service":"dns-filter","timestamp":"%s"}`, time.Now().Format(time.RFC3339))
	}).Methods("GET")

	// Metrics endpoint
	router.Handle("/metrics", promhttp.Handler())

	// Ready check endpoint
	router.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		// Check if DNS server is ready
		if !dnsServer.IsReady() {
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintf(w, `{"status":"not ready","service":"dns-filter"}`)
			return
		}
		
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"ready","service":"dns-filter"}`)
	}).Methods("GET")

	httpServer := &http.Server{
		Addr:         cfg.HTTPAddress,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start HTTP server in goroutine
	go func() {
		log.Info("Starting HTTP server", "address", cfg.HTTPAddress)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("HTTP server failed to start", "error", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("Shutting down servers...")

	// Create shutdown context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Shutdown HTTP server
	if err := httpServer.Shutdown(ctx); err != nil {
		log.Error("HTTP server forced to shutdown", "error", err)
	}

	// Shutdown DNS server
	if err := dnsServer.Shutdown(ctx); err != nil {
		log.Error("DNS server forced to shutdown", "error", err)
	}

	log.Info("GuardNet DNS Filter Service stopped")
}