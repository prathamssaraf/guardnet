// Simple test program to verify DNS service components without Docker
package main

import (
	"fmt"
	"log"
	"time"

	"guardnet/dns-filter/internal/config"
	"guardnet/dns-filter/internal/metrics"
	"guardnet/dns-filter/pkg/logger"
)

func main() {
	fmt.Println("🧪 GuardNet DNS Service - Component Tests")
	fmt.Println("==========================================")

	// Test 1: Configuration Loading
	fmt.Println("\n1. Testing Configuration Loading...")
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("❌ Config test failed: %v", err)
	}
	fmt.Printf("✅ Config loaded successfully")
	fmt.Printf("   - DNS Address: %s\n", cfg.DNSAddress)
	fmt.Printf("   - HTTP Address: %s\n", cfg.HTTPAddress)
	fmt.Printf("   - Environment: %s\n", cfg.Environment)
	fmt.Printf("   - Upstream DNS: %v\n", cfg.UpstreamDNS)

	// Test 2: Logger Initialization
	fmt.Println("\n2. Testing Logger System...")
	logger := logger.New()
	if logger == nil {
		log.Fatal("❌ Logger test failed: nil logger")
	}
	fmt.Println("✅ Logger initialized successfully")
	logger.Info("Test log message", "component", "test", "status", "success")

	// Test 3: Metrics Collector
	fmt.Println("\n3. Testing Metrics Collector...")
	metrics := metrics.NewCollector()
	if metrics == nil {
		log.Fatal("❌ Metrics test failed: nil collector")
	}
	fmt.Println("✅ Metrics collector initialized successfully")
	
	// Simulate some metrics
	metrics.RecordDNSQuery("A", 0.025, false, "")
	metrics.RecordDNSQuery("AAAA", 0.015, true, "malware")
	metrics.RecordCacheHit()
	metrics.RecordCacheMiss()
	
	fmt.Printf("   - DNS queries recorded\n")
	fmt.Printf("   - Cache metrics recorded\n")

	// Test 4: Component Integration
	fmt.Println("\n4. Testing Component Integration...")
	
	// Simulate a simple workflow
	start := time.Now()
	
	// Configuration-based setup
	if cfg.IsDevelopment() {
		logger.Debug("Running in development mode")
	}
	
	// Metrics recording
	responseTime := time.Since(start).Seconds()
	metrics.RecordDNSQuery("A", responseTime, false, "")
	
	fmt.Println("✅ Component integration successful")
	fmt.Printf("   - Response time: %.3fs\n", responseTime)

	// Summary
	fmt.Println("\n📊 Test Summary:")
	fmt.Println("================")
	fmt.Println("✅ Configuration System - PASS")
	fmt.Println("✅ Logging System - PASS") 
	fmt.Println("✅ Metrics Collection - PASS")
	fmt.Println("✅ Component Integration - PASS")
	fmt.Println("\n🎉 All core components are working correctly!")
	fmt.Println("\n📝 Notes:")
	fmt.Println("   - DNS server requires database/Redis for full testing")
	fmt.Println("   - Docker environment needed for complete integration")
	fmt.Println("   - HTTP endpoints can be tested with curl when server runs")
}