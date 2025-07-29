// Simple HTTP server test to verify health and metrics endpoints
package main

import (
	"fmt"
	"net/http"
	"time"

	"guardnet/dns-filter/internal/config"
	"guardnet/dns-filter/internal/metrics"
	"guardnet/dns-filter/pkg/logger"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	fmt.Println("🌐 GuardNet HTTP Endpoints Test")
	fmt.Println("================================")

	// Initialize components
	logger := logger.New()
	metricsCollector := metrics.NewCollector()

	// Setup HTTP server with the same endpoints as main server
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
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"ready","service":"dns-filter"}`)
	}).Methods("GET")

	// Test endpoint for demonstration
	router.HandleFunc("/test", func(w http.ResponseWriter, r *http.Request) {
		// Record some test metrics
		metricsCollector.RecordDNSQuery("A", 0.025, false, "")
		metricsCollector.RecordCacheHit()
		
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"message":"Test endpoint working","metrics_recorded":true}`)
	}).Methods("GET")

	// Use a different port for testing to avoid conflicts
	testPort := ":8081"
	httpServer := &http.Server{
		Addr:         testPort,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Info("Starting HTTP test server", "port", testPort)
	fmt.Printf("🚀 Server starting on port %s\n", testPort)
	fmt.Println("\n📡 Available endpoints:")
	fmt.Printf("   - Health Check: http://localhost%s/health\n", testPort)
	fmt.Printf("   - Metrics:      http://localhost%s/metrics\n", testPort)
	fmt.Printf("   - Ready Check:  http://localhost%s/ready\n", testPort)
	fmt.Printf("   - Test:         http://localhost%s/test\n", testPort)
	
	fmt.Println("\n🔥 Server is running! Test the endpoints in your browser or with curl.")
	fmt.Println("   Press Ctrl+C to stop")

	if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Fatal("HTTP server failed to start", "error", err)
	}
}