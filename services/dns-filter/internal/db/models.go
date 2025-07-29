package db

import "time"

// User represents a user in the system
type User struct {
	ID               string    `json:"id"`
	Email            string    `json:"email"`
	FirstName        string    `json:"first_name"`
	LastName         string    `json:"last_name"`
	SubscriptionTier string    `json:"subscription_tier"`
	IsActive         bool      `json:"is_active"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

// Router represents a router configuration
type Router struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	RouterMAC   string                 `json:"router_mac"`
	RouterModel string                 `json:"router_model"`
	DNSConfig   map[string]interface{} `json:"dns_config"`
	IsActive    bool                   `json:"is_active"`
	LastSeen    *time.Time             `json:"last_seen"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// ThreatDomain represents a domain in the threat intelligence database
type ThreatDomain struct {
	ID              string    `json:"id"`
	Domain          string    `json:"domain"`
	ThreatType      string    `json:"threat_type"`
	ConfidenceScore float64   `json:"confidence_score"`
	Source          string    `json:"source"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

// DNSLog represents a logged DNS query
type DNSLog struct {
	ID           string    `json:"id"`
	RouterID     string    `json:"router_id"`
	Domain       string    `json:"domain"`
	QueryType    string    `json:"query_type"`
	ResponseType string    `json:"response_type"`
	ThreatType   string    `json:"threat_type"`
	Timestamp    time.Time `json:"timestamp"`
}

// ThreatStats represents aggregated threat statistics
type ThreatStats struct {
	TotalQueries   int64 `json:"total_queries"`
	BlockedQueries int64 `json:"blocked_queries"`
	AllowedQueries int64 `json:"allowed_queries"`
	UniqueDomains  int64 `json:"unique_domains"`
}

// ThreatInfo represents information about a specific threat
type ThreatInfo struct {
	Domain     string `json:"domain"`
	ThreatType string `json:"threat_type"`
	Count      int64  `json:"count"`
}

// SubscriptionPlan represents a subscription plan
type SubscriptionPlan struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	PriceMonthly float64                `json:"price_monthly"`
	Features     map[string]interface{} `json:"features"`
	IsActive     bool                   `json:"is_active"`
	CreatedAt    time.Time              `json:"created_at"`
}

// UserSubscription represents a user's subscription
type UserSubscription struct {
	ID        string     `json:"id"`
	UserID    string     `json:"user_id"`
	PlanID    string     `json:"plan_id"`
	Status    string     `json:"status"`
	StartedAt time.Time  `json:"started_at"`
	ExpiresAt *time.Time `json:"expires_at"`
	CreatedAt time.Time  `json:"created_at"`
}