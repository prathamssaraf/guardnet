package db

import (
	"fmt"
	"time"
)

// MockConnection implements a mock database for testing without PostgreSQL
type MockConnection struct {
	threatDomains map[string]string
	queryLogs     []DNSLog
}

// NewMockConnection creates a mock database connection for testing
func NewMockConnection() *MockConnection {
	return &MockConnection{
		threatDomains: map[string]string{
			"malware-test.com":     "malware",
			"phishing-example.org": "phishing", 
			"doubleclick.net":      "ads",
			"googleadservices.com": "ads",
			"facebook.com":         "ads", // For testing
		},
		queryLogs: make([]DNSLog, 0),
	}
}

// Close implements the Close method (no-op for mock)
func (m *MockConnection) Close() error {
	return nil
}

// CheckThreatDomain checks if a domain exists in the mock threat database
func (m *MockConnection) CheckThreatDomain(domain string) (string, error) {
	if threatType, exists := m.threatDomains[domain]; exists {
		return threatType, nil
	}
	return "", nil // Domain not found in threat database
}

// LogDNSQuery logs a DNS query to the mock database
func (m *MockConnection) LogDNSQuery(clientIP, domain, queryType, responseType, threatType string) error {
	log := DNSLog{
		ID:           fmt.Sprintf("mock-%d", len(m.queryLogs)+1),
		RouterID:     "mock-router-id",
		Domain:       domain,
		QueryType:    queryType,
		ResponseType: responseType,
		ThreatType:   threatType,
		Timestamp:    time.Now(),
	}
	m.queryLogs = append(m.queryLogs, log)
	return nil
}

// GetUserByRouterMAC returns a mock user for testing
func (m *MockConnection) GetUserByRouterMAC(macAddress string) (*User, error) {
	return &User{
		ID:               "mock-user-id",
		Email:            "test@guardnet.com",
		FirstName:        "Test",
		LastName:         "User",
		SubscriptionTier: "pro",
		IsActive:         true,
	}, nil
}

// UpdateRouterLastSeen updates the last seen timestamp (no-op for mock)
func (m *MockConnection) UpdateRouterLastSeen(macAddress string) error {
	return nil
}

// GetThreatStats returns mock threat statistics
func (m *MockConnection) GetThreatStats(since time.Time) (*ThreatStats, error) {
	return &ThreatStats{
		TotalQueries:   int64(len(m.queryLogs)),
		BlockedQueries: 15,
		AllowedQueries: int64(len(m.queryLogs)) - 15,
		UniqueDomains:  10,
	}, nil
}

// GetTopThreats returns mock top threats
func (m *MockConnection) GetTopThreats(since time.Time, limit int) ([]ThreatInfo, error) {
	return []ThreatInfo{
		{Domain: "malware-test.com", ThreatType: "malware", Count: 5},
		{Domain: "phishing-example.org", ThreatType: "phishing", Count: 3},
		{Domain: "doubleclick.net", ThreatType: "ads", Count: 2},
	}, nil
}

// GetQueryLogs returns all logged queries for inspection
func (m *MockConnection) GetQueryLogs() []DNSLog {
	return m.queryLogs
}

// AddThreatDomain adds a domain to the threat database for testing
func (m *MockConnection) AddThreatDomain(domain, threatType string) {
	m.threatDomains[domain] = threatType
}