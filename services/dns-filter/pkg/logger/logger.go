package logger

import (
	"os"

	"github.com/sirupsen/logrus"
)

// Logger wraps logrus.Logger with structured logging
type Logger struct {
	*logrus.Logger
}

// New creates a new logger instance
func New() *Logger {
	log := logrus.New()
	
	// Set output to stdout
	log.SetOutput(os.Stdout)
	
	// Set JSON formatter for production, text for development
	if os.Getenv("GO_ENV") == "production" {
		log.SetFormatter(&logrus.JSONFormatter{})
	} else {
		log.SetFormatter(&logrus.TextFormatter{
			FullTimestamp: true,
			ForceColors:   true,
		})
	}
	
	// Set log level
	level := os.Getenv("LOG_LEVEL")
	switch level {
	case "debug":
		log.SetLevel(logrus.DebugLevel)
	case "warn":
		log.SetLevel(logrus.WarnLevel)
	case "error":
		log.SetLevel(logrus.ErrorLevel)
	case "fatal":
		log.SetLevel(logrus.FatalLevel)
	default:
		log.SetLevel(logrus.InfoLevel)
	}
	
	return &Logger{log}
}

// WithFields creates a new logger entry with structured fields
func (l *Logger) WithFields(fields map[string]interface{}) *logrus.Entry {
	return l.Logger.WithFields(logrus.Fields(fields))
}

// WithError creates a new logger entry with an error field
func (l *Logger) WithError(err error) *logrus.Entry {
	return l.Logger.WithError(err)
}

// Info logs an info message with optional key-value pairs
func (l *Logger) Info(msg string, keysAndValues ...interface{}) {
	l.logWithFields(logrus.InfoLevel, msg, keysAndValues...)
}

// Debug logs a debug message with optional key-value pairs
func (l *Logger) Debug(msg string, keysAndValues ...interface{}) {
	l.logWithFields(logrus.DebugLevel, msg, keysAndValues...)
}

// Warn logs a warning message with optional key-value pairs
func (l *Logger) Warn(msg string, keysAndValues ...interface{}) {
	l.logWithFields(logrus.WarnLevel, msg, keysAndValues...)
}

// Error logs an error message with optional key-value pairs
func (l *Logger) Error(msg string, keysAndValues ...interface{}) {
	l.logWithFields(logrus.ErrorLevel, msg, keysAndValues...)
}

// Fatal logs a fatal message with optional key-value pairs and exits
func (l *Logger) Fatal(msg string, keysAndValues ...interface{}) {
	l.logWithFields(logrus.FatalLevel, msg, keysAndValues...)
}

// logWithFields logs a message with structured fields
func (l *Logger) logWithFields(level logrus.Level, msg string, keysAndValues ...interface{}) {
	fields := logrus.Fields{}
	
	// Parse key-value pairs
	for i := 0; i < len(keysAndValues); i += 2 {
		if i+1 < len(keysAndValues) {
			key := keysAndValues[i]
			value := keysAndValues[i+1]
			if keyStr, ok := key.(string); ok {
				fields[keyStr] = value
			}
		}
	}
	
	l.Logger.WithFields(fields).Log(level, msg)
}