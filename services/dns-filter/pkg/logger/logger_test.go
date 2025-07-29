package logger

import (
	"testing"
)

func TestNew(t *testing.T) {
	logger := New()
	if logger == nil {
		t.Fatal("Expected logger to be created, got nil")
	}

	if logger.Logger == nil {
		t.Fatal("Expected internal logger to be created, got nil")
	}
}

func TestWithFields(t *testing.T) {
	logger := New()
	
	fields := map[string]interface{}{
		"user_id": "12345",
		"action":  "login",
	}
	
	entry := logger.WithFields(fields)
	if entry == nil {
		t.Fatal("Expected entry to be created, got nil")
	}
}

func TestLoggingMethods(t *testing.T) {
	logger := New()
	
	// These shouldn't panic
	logger.Info("Test info message", "key", "value")
	logger.Debug("Test debug message", "key", "value")
	logger.Warn("Test warn message", "key", "value")
	logger.Error("Test error message", "key", "value")
}