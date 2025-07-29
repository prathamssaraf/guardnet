package config

import (
	"os"
	"strconv"
)

// Config holds all configuration for the DNS filter service
type Config struct {
	// Server addresses
	DNSAddress  string
	HTTPAddress string
	
	// Database configuration
	DatabaseURL string
	
	// Cache configuration
	RedisURL string
	
	// DNS configuration
	UpstreamDNS    []string
	BlockedDomains []string
	
	// Security settings
	RateLimitPerSecond int
	MaxQueriesPerIP    int
	
	// Logging
	LogLevel string
	
	// Environment
	Environment string
}

// Load loads configuration from environment variables with defaults
func Load() (*Config, error) {
	cfg := &Config{
		// Default server addresses
		DNSAddress:  getEnv("DNS_ADDRESS", ":53"),
		HTTPAddress: getEnv("HTTP_ADDRESS", ":8080"),
		
		// Database
		DatabaseURL: getEnv("DATABASE_URL", "postgres://guardnet:dev-password@postgres:5432/guardnet?sslmode=disable"),
		
		// Cache
		RedisURL: getEnv("REDIS_URL", "redis://redis:6379"),
		
		// DNS settings
		UpstreamDNS: []string{
			getEnv("UPSTREAM_DNS_1", "1.1.1.1:53"),    // Cloudflare
			getEnv("UPSTREAM_DNS_2", "8.8.8.8:53"),    // Google
		},
		
		// Rate limiting
		RateLimitPerSecond: getEnvAsInt("RATE_LIMIT_PER_SECOND", 100),
		MaxQueriesPerIP:    getEnvAsInt("MAX_QUERIES_PER_IP", 1000),
		
		// Logging
		LogLevel: getEnv("LOG_LEVEL", "info"),
		
		// Environment
		Environment: getEnv("GO_ENV", "development"),
	}
	
	return cfg, nil
}

// getEnv gets an environment variable with a fallback value
func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

// getEnvAsInt gets an environment variable as integer with a fallback value
func getEnvAsInt(key string, fallback int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return fallback
}

// IsDevelopment returns true if running in development environment
func (c *Config) IsDevelopment() bool {
	return c.Environment == "development"
}

// IsProduction returns true if running in production environment
func (c *Config) IsProduction() bool {
	return c.Environment == "production"
}