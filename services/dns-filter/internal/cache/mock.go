package cache

import (
	"fmt"
	"sync"
	"time"
)

// MockRedisClient implements a mock Redis client for testing without Redis
type MockRedisClient struct {
	data   map[string]mockValue
	mutex  sync.RWMutex
	closed bool
}

type mockValue struct {
	value      string
	expiration time.Time
}

// NewMockRedisClient creates a new mock Redis client
func NewMockRedisClient() *MockRedisClient {
	return &MockRedisClient{
		data:   make(map[string]mockValue),
		closed: false,
	}
}

// Close closes the mock Redis connection
func (m *MockRedisClient) Close() error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	m.closed = true
	return nil
}

// Get retrieves a value from the mock cache
func (m *MockRedisClient) Get(key string) (string, error) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	if m.closed {
		return "", fmt.Errorf("client is closed")
	}
	
	value, exists := m.data[key]
	if !exists {
		return "", fmt.Errorf("key not found: %s", key)
	}
	
	// Check if expired
	if !value.expiration.IsZero() && time.Now().After(value.expiration) {
		delete(m.data, key)
		return "", fmt.Errorf("key not found: %s", key)
	}
	
	return value.value, nil
}

// Set stores a value in the mock cache with expiration
func (m *MockRedisClient) Set(key, value string, expiration time.Duration) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	if m.closed {
		return fmt.Errorf("client is closed")
	}
	
	var exp time.Time
	if expiration > 0 {
		exp = time.Now().Add(expiration)
	}
	
	m.data[key] = mockValue{
		value:      value,
		expiration: exp,
	}
	
	return nil
}

// Delete removes a key from the mock cache
func (m *MockRedisClient) Delete(key string) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	if m.closed {
		return fmt.Errorf("client is closed")
	}
	
	delete(m.data, key)
	return nil
}

// Exists checks if a key exists in the mock cache
func (m *MockRedisClient) Exists(key string) (bool, error) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	if m.closed {
		return false, fmt.Errorf("client is closed")
	}
	
	value, exists := m.data[key]
	if !exists {
		return false, nil
	}
	
	// Check if expired
	if !value.expiration.IsZero() && time.Now().After(value.expiration) {
		delete(m.data, key)
		return false, nil
	}
	
	return true, nil
}

// SetNX sets a key only if it doesn't exist
func (m *MockRedisClient) SetNX(key, value string, expiration time.Duration) (bool, error) {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	if m.closed {
		return false, fmt.Errorf("client is closed")
	}
	
	// Check if key already exists and is not expired
	if existing, exists := m.data[key]; exists {
		if existing.expiration.IsZero() || time.Now().Before(existing.expiration) {
			return false, nil // Key already exists
		}
	}
	
	var exp time.Time
	if expiration > 0 {
		exp = time.Now().Add(expiration)
	}
	
	m.data[key] = mockValue{
		value:      value,
		expiration: exp,
	}
	
	return true, nil
}

// Increment increments a counter in the mock cache
func (m *MockRedisClient) Increment(key string) (int64, error) {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	if m.closed {
		return 0, fmt.Errorf("client is closed")
	}
	
	value, exists := m.data[key]
	var count int64 = 1
	
	if exists {
		if !value.expiration.IsZero() && time.Now().After(value.expiration) {
			// Key expired, start from 1
			count = 1
		} else {
			// Parse existing value and increment
			if existing, err := parseInt64(value.value); err == nil {
				count = existing + 1
			}
		}
	}
	
	m.data[key] = mockValue{
		value:      fmt.Sprintf("%d", count),
		expiration: value.expiration,
	}
	
	return count, nil
}

// IncrementWithExpiry increments a counter and sets expiry
func (m *MockRedisClient) IncrementWithExpiry(key string, expiration time.Duration) (int64, error) {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	if m.closed {
		return 0, fmt.Errorf("client is closed")
	}
	
	value, exists := m.data[key]
	var count int64 = 1
	
	if exists && (value.expiration.IsZero() || time.Now().Before(value.expiration)) {
		if existing, err := parseInt64(value.value); err == nil {
			count = existing + 1
		}
	}
	
	var exp time.Time
	if expiration > 0 {
		exp = time.Now().Add(expiration)
	}
	
	m.data[key] = mockValue{
		value:      fmt.Sprintf("%d", count),
		expiration: exp,
	}
	
	return count, nil
}

// GetTTL returns the time to live for a key
func (m *MockRedisClient) GetTTL(key string) (time.Duration, error) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	if m.closed {
		return 0, fmt.Errorf("client is closed")
	}
	
	value, exists := m.data[key]
	if !exists {
		return -2 * time.Second, nil // Key doesn't exist
	}
	
	if value.expiration.IsZero() {
		return -1 * time.Second, nil // Key exists but has no expiration
	}
	
	ttl := time.Until(value.expiration)
	if ttl <= 0 {
		delete(m.data, key)
		return -2 * time.Second, nil // Key expired
	}
	
	return ttl, nil
}

// Remaining methods with basic implementations for completeness

func (m *MockRedisClient) SetHash(key string, fields map[string]interface{}) error {
	// Simplified hash implementation - just store as JSON-like string
	return m.Set(key, fmt.Sprintf("%v", fields), 0)
}

func (m *MockRedisClient) GetHash(key string) (map[string]string, error) {
	// Simplified - return empty map
	return make(map[string]string), nil
}

func (m *MockRedisClient) GetHashField(key, field string) (string, error) {
	return "", fmt.Errorf("hash field not found: %s.%s", key, field)
}

func (m *MockRedisClient) AddToSet(key, member string) error {
	return m.Set(fmt.Sprintf("%s:set:%s", key, member), "1", 0)
}

func (m *MockRedisClient) IsInSet(key, member string) (bool, error) {
	exists, err := m.Exists(fmt.Sprintf("%s:set:%s", key, member))
	return exists, err
}

func (m *MockRedisClient) GetSetMembers(key string) ([]string, error) {
	return []string{}, nil
}

func (m *MockRedisClient) FlushDB() error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	m.data = make(map[string]mockValue)
	return nil
}

func (m *MockRedisClient) GetInfo() (string, error) {
	return "Mock Redis Client - In Memory", nil
}

// Helper function to parse int64
func parseInt64(s string) (int64, error) {
	var result int64
	for _, c := range s {
		if c < '0' || c > '9' {
			return 0, fmt.Errorf("invalid number")
		}
		result = result*10 + int64(c-'0')
	}
	return result, nil
}