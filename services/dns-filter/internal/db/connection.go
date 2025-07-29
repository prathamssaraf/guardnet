package db

import (
	"database/sql"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

// Connection represents a database connection with query methods
type Connection struct {
	db *sql.DB
}

// NewConnection creates a new database connection
func NewConnection(databaseURL string) (*Connection, error) {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)
	db.SetConnMaxIdleTime(time.Minute)

	// Test the connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &Connection{db: db}, nil
}

// Close closes the database connection
func (c *Connection) Close() error {
	if c.db != nil {
		return c.db.Close()
	}
	return nil
}

// CheckThreatDomain checks if a domain exists in the threat database
func (c *Connection) CheckThreatDomain(domain string) (string, error) {
	query := `
		SELECT threat_type 
		FROM threat_domains 
		WHERE domain = $1 AND confidence_score > 0.7
		LIMIT 1
	`
	
	var threatType string
	err := c.db.QueryRow(query, domain).Scan(&threatType)
	if err != nil {
		if err == sql.ErrNoRows {
			// Domain not found in threat database
			return "", nil
		}
		return "", fmt.Errorf("failed to query threat domain: %w", err)
	}
	
	return threatType, nil
}

// LogDNSQuery logs a DNS query to the database
func (c *Connection) LogDNSQuery(clientIP, domain, queryType, responseType, threatType string) error {
	// First, try to find the router by client IP (simplified lookup)
	var routerID string
	routerQuery := `
		SELECT id FROM routers 
		WHERE last_seen > NOW() - INTERVAL '1 hour' 
		LIMIT 1
	`
	
	err := c.db.QueryRow(routerQuery).Scan(&routerID)
	if err != nil {
		// If no router found, use a default UUID or skip logging
		routerID = "00000000-0000-0000-0000-000000000000"
	}

	// Insert DNS log entry
	insertQuery := `
		INSERT INTO dns_logs (router_id, domain, query_type, response_type, threat_type, timestamp)
		VALUES ($1, $2, $3, $4, $5, NOW())
	`
	
	_, err = c.db.Exec(insertQuery, routerID, domain, queryType, responseType, threatType)
	if err != nil {
		return fmt.Errorf("failed to log DNS query: %w", err)
	}
	
	return nil
}

// GetUserByRouterMAC retrieves user information by router MAC address
func (c *Connection) GetUserByRouterMAC(macAddress string) (*User, error) {
	query := `
		SELECT u.id, u.email, u.first_name, u.last_name, u.subscription_tier, u.is_active
		FROM users u
		JOIN routers r ON u.id = r.user_id
		WHERE r.router_mac = $1 AND r.is_active = true AND u.is_active = true
	`
	
	user := &User{}
	err := c.db.QueryRow(query, macAddress).Scan(
		&user.ID, &user.Email, &user.FirstName, &user.LastName, 
		&user.SubscriptionTier, &user.IsActive,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get user by router MAC: %w", err)
	}
	
	return user, nil
}

// UpdateRouterLastSeen updates the last seen timestamp for a router
func (c *Connection) UpdateRouterLastSeen(macAddress string) error {
	query := `UPDATE routers SET last_seen = NOW() WHERE router_mac = $1`
	
	_, err := c.db.Exec(query, macAddress)
	if err != nil {
		return fmt.Errorf("failed to update router last seen: %w", err)
	}
	
	return nil
}

// GetThreatStats returns threat statistics for analytics
func (c *Connection) GetThreatStats(since time.Time) (*ThreatStats, error) {
	query := `
		SELECT 
			COUNT(*) as total_queries,
			COUNT(CASE WHEN response_type = 'blocked' THEN 1 END) as blocked_queries,
			COUNT(CASE WHEN response_type = 'allowed' THEN 1 END) as allowed_queries,
			COUNT(DISTINCT domain) as unique_domains
		FROM dns_logs 
		WHERE timestamp >= $1
	`
	
	stats := &ThreatStats{}
	err := c.db.QueryRow(query, since).Scan(
		&stats.TotalQueries, &stats.BlockedQueries, 
		&stats.AllowedQueries, &stats.UniqueDomains,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get threat stats: %w", err)
	}
	
	return stats, nil
}

// GetTopThreats returns the most common threats in a time period
func (c *Connection) GetTopThreats(since time.Time, limit int) ([]ThreatInfo, error) {
	query := `
		SELECT domain, threat_type, COUNT(*) as count
		FROM dns_logs 
		WHERE timestamp >= $1 AND response_type = 'blocked' AND threat_type != ''
		GROUP BY domain, threat_type
		ORDER BY count DESC
		LIMIT $2
	`
	
	rows, err := c.db.Query(query, since, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get top threats: %w", err)
	}
	defer rows.Close()
	
	var threats []ThreatInfo
	for rows.Next() {
		threat := ThreatInfo{}
		err := rows.Scan(&threat.Domain, &threat.ThreatType, &threat.Count)
		if err != nil {
			return nil, fmt.Errorf("failed to scan threat info: %w", err)
		}
		threats = append(threats, threat)
	}
	
	return threats, nil
}