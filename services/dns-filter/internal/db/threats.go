package db

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"guardnet/dns-filter/internal/feeds"

	"github.com/lib/pq"
	"github.com/sirupsen/logrus"
)

// ThreatDB handles threat domain database operations
type ThreatDB struct {
	db     *sql.DB
	logger *logrus.Logger
}

// NewThreatDB creates a new threat database connection
func NewThreatDB(dbURL string, logger *logrus.Logger) (*ThreatDB, error) {
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, fmt.Errorf("opening database: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("pinging database: %w", err)
	}

	logger.Info("Connected to PostgreSQL threat database")

	return &ThreatDB{
		db:     db,
		logger: logger,
	}, nil
}

// IsThreatDomain checks if a domain is in the threat database
func (tdb *ThreatDB) IsThreatDomain(ctx context.Context, domain string) (bool, string, float64, error) {
	query := `
		SELECT threat_type, confidence_score 
		FROM threat_domains 
		WHERE domain = $1 AND created_at > NOW() - INTERVAL '30 days'
		ORDER BY confidence_score DESC 
		LIMIT 1
	`

	var threatType string
	var confidence float64

	err := tdb.db.QueryRowContext(ctx, query, domain).Scan(&threatType, &confidence)
	if err != nil {
		if err == sql.ErrNoRows {
			return false, "", 0, nil
		}
		return false, "", 0, fmt.Errorf("querying threat domain: %w", err)
	}

	return true, threatType, confidence, nil
}

// BatchInsertThreats inserts multiple threat entries efficiently
func (tdb *ThreatDB) BatchInsertThreats(ctx context.Context, entries []feeds.ThreatEntry) error {
	if len(entries) == 0 {
		return nil
	}

	// Use PostgreSQL COPY for efficient bulk insert
	txn, err := tdb.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("beginning transaction: %w", err)
	}
	defer txn.Rollback()

	// Prepare COPY statement
	stmt, err := txn.PrepareContext(ctx, pq.CopyIn("threat_domains",
		"domain", "threat_type", "confidence_score", "source", "created_at", "updated_at"))
	if err != nil {
		return fmt.Errorf("preparing COPY statement: %w", err)
	}

	now := time.Now()
	inserted := 0

	for _, entry := range entries {
		_, err = stmt.ExecContext(ctx,
			entry.Domain,
			entry.ThreatType,
			entry.Confidence,
			entry.Source,
			now,
			now,
		)
		if err != nil {
			// Log error but continue with other entries
			tdb.logger.WithError(err).WithFields(logrus.Fields{
				"domain": entry.Domain,
				"source": entry.Source,
			}).Warn("Failed to insert threat entry")
			continue
		}
		inserted++
	}

	// Execute the COPY
	_, err = stmt.ExecContext(ctx)
	if err != nil {
		return fmt.Errorf("executing COPY: %w", err)
	}

	if err = stmt.Close(); err != nil {
		return fmt.Errorf("closing COPY statement: %w", err)
	}

	if err = txn.Commit(); err != nil {
		return fmt.Errorf("committing transaction: %w", err)
	}

	tdb.logger.WithFields(logrus.Fields{
		"inserted": inserted,
		"total":    len(entries),
	}).Info("Batch inserted threat domains")

	return nil
}

// UpdateThreatEntry updates an existing threat entry
func (tdb *ThreatDB) UpdateThreatEntry(ctx context.Context, entry feeds.ThreatEntry) error {
	query := `
		INSERT INTO threat_domains (domain, threat_type, confidence_score, source, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (domain) 
		DO UPDATE SET 
			threat_type = EXCLUDED.threat_type,
			confidence_score = GREATEST(threat_domains.confidence_score, EXCLUDED.confidence_score),
			source = EXCLUDED.source,
			updated_at = EXCLUDED.updated_at
	`

	now := time.Now()
	_, err := tdb.db.ExecContext(ctx, query,
		entry.Domain,
		entry.ThreatType,
		entry.Confidence,
		entry.Source,
		now,
		now,
	)

	if err != nil {
		return fmt.Errorf("upserting threat entry: %w", err)
	}

	return nil
}

// GetThreatStats returns threat statistics
func (tdb *ThreatDB) GetThreatStats(ctx context.Context) (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	// Total threat domains
	var totalThreats int
	err := tdb.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM threat_domains").Scan(&totalThreats)
	if err != nil {
		return nil, fmt.Errorf("getting total threats: %w", err)
	}
	stats["total_threats"] = totalThreats

	// Threats by type
	threatsByType := make(map[string]int)
	rows, err := tdb.db.QueryContext(ctx, `
		SELECT threat_type, COUNT(*) 
		FROM threat_domains 
		GROUP BY threat_type
	`)
	if err != nil {
		return nil, fmt.Errorf("getting threats by type: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var threatType string
		var count int
		if err := rows.Scan(&threatType, &count); err != nil {
			continue
		}
		threatsByType[threatType] = count
	}
	stats["threats_by_type"] = threatsByType

	// Recent threats (last 24 hours)
	var recentThreats int
	err = tdb.db.QueryRowContext(ctx, `
		SELECT COUNT(*) 
		FROM threat_domains 
		WHERE created_at > NOW() - INTERVAL '24 hours'
	`).Scan(&recentThreats)
	if err != nil {
		return nil, fmt.Errorf("getting recent threats: %w", err)
	}
	stats["recent_threats_24h"] = recentThreats

	// Top sources
	topSources := make(map[string]int)
	rows, err = tdb.db.QueryContext(ctx, `
		SELECT source, COUNT(*) 
		FROM threat_domains 
		GROUP BY source 
		ORDER BY COUNT(*) DESC 
		LIMIT 10
	`)
	if err != nil {
		return nil, fmt.Errorf("getting top sources: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var source string
		var count int
		if err := rows.Scan(&source, &count); err != nil {
			continue
		}
		topSources[source] = count
	}
	stats["top_sources"] = topSources

	return stats, nil
}

// LogDNSQuery logs a DNS query for analytics
func (tdb *ThreatDB) LogDNSQuery(ctx context.Context, domain, queryType, responseType, threatType string, responseTimeMs int, clientIP string) error {
	query := `
		INSERT INTO dns_logs (domain, query_type, response_type, threat_type, timestamp)
		VALUES ($1, $2, $3, NULLIF($4, ''), $5)
	`

	_, err := tdb.db.ExecContext(ctx, query, domain, queryType, responseType, threatType, time.Now())
	if err != nil {
		return fmt.Errorf("logging DNS query: %w", err)
	}

	return nil
}

// CleanupOldThreats removes old threat entries
func (tdb *ThreatDB) CleanupOldThreats(ctx context.Context, maxAge time.Duration) error {
	query := `
		DELETE FROM threat_domains 
		WHERE updated_at < $1
	`

	cutoff := time.Now().Add(-maxAge)
	result, err := tdb.db.ExecContext(ctx, query, cutoff)
	if err != nil {
		return fmt.Errorf("cleaning up old threats: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	tdb.logger.WithFields(logrus.Fields{
		"deleted": rowsAffected,
		"cutoff":  cutoff,
	}).Info("Cleaned up old threat entries")

	return nil
}

// Close closes the database connection
func (tdb *ThreatDB) Close() error {
	return tdb.db.Close()
}