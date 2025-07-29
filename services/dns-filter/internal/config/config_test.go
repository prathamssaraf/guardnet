package config

import (
	"os"
	"testing"
)

func TestLoad(t *testing.T) {
	// Test default configuration
	cfg, err := Load()
	if err != nil {
		t.Fatalf("Failed to load default config: %v", err)
	}

	// Check default values
	if cfg.DNSAddress != ":53" {
		t.Errorf("Expected DNS address :53, got %s", cfg.DNSAddress)
	}

	if cfg.HTTPAddress != ":8080" {
		t.Errorf("Expected HTTP address :8080, got %s", cfg.HTTPAddress)
	}

	if len(cfg.UpstreamDNS) != 2 {
		t.Errorf("Expected 2 upstream DNS servers, got %d", len(cfg.UpstreamDNS))
	}
}

func TestLoadWithEnvironment(t *testing.T) {
	// Set environment variables
	os.Setenv("DNS_ADDRESS", ":1053")
	os.Setenv("LOG_LEVEL", "debug")
	defer func() {
		os.Unsetenv("DNS_ADDRESS")
		os.Unsetenv("LOG_LEVEL")
	}()

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Failed to load config with env vars: %v", err)
	}

	if cfg.DNSAddress != ":1053" {
		t.Errorf("Expected DNS address :1053, got %s", cfg.DNSAddress)
	}

	if cfg.LogLevel != "debug" {
		t.Errorf("Expected log level debug, got %s", cfg.LogLevel)
	}
}

func TestIsDevelopment(t *testing.T) {
	cfg := &Config{Environment: "development"}
	if !cfg.IsDevelopment() {
		t.Error("Expected IsDevelopment() to return true")
	}

	cfg.Environment = "production"
	if cfg.IsDevelopment() {
		t.Error("Expected IsDevelopment() to return false")
	}
}

func TestIsProduction(t *testing.T) {
	cfg := &Config{Environment: "production"}
	if !cfg.IsProduction() {
		t.Error("Expected IsProduction() to return true")
	}

	cfg.Environment = "development"
	if cfg.IsProduction() {
		t.Error("Expected IsProduction() to return false")
	}
}