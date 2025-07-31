package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"guardnet/dns-filter/internal/config"
	"guardnet/dns-filter/internal/db"
	"guardnet/dns-filter/internal/feeds"
	"guardnet/dns-filter/pkg/logger"

	"github.com/sirupsen/logrus"
)

// ThreatUpdater manages periodic threat intelligence updates
type ThreatUpdater struct {
	feedManager     *feeds.FeedManager
	adBlockManager  *feeds.AdBlockManager
	threatDB        *db.ThreatDB
	logger          *logrus.Logger
	updateChan      chan struct{}
}

func main() {
	// Initialize logger
	log := logger.New()
	log.Info("Starting GuardNet Threat Intelligence Updater")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.WithError(err).Fatal("Failed to load configuration")
	}

	// Initialize database connection
	dbURL := fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=disable",
		cfg.Database.User,
		cfg.Database.Password,
		cfg.Database.Host,
		cfg.Database.Port,
		cfg.Database.Name,
	)

	threatDB, err := db.NewThreatDB(dbURL, log.Logger)
	if err != nil {
		log.WithError(err).Fatal("Failed to connect to threat database")
	}
	defer threatDB.Close()

	// Initialize feed managers
	feedManager := feeds.NewFeedManager(log.Logger)
	adBlockManager := feeds.NewAdBlockManager(log.Logger)

	// Create threat updater
	updater := &ThreatUpdater{
		feedManager:    feedManager,
		adBlockManager: adBlockManager,
		threatDB:       threatDB,
		logger:         log.Logger,
		updateChan:     make(chan struct{}, 1),
	}

	// Start periodic updates
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle shutdown signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Trigger initial update
	updater.updateChan <- struct{}{}

	log.Info("Threat updater started, waiting for updates...")

	for {
		select {
		case <-ctx.Done():
			log.Info("Context cancelled, shutting down")
			return

		case <-sigChan:
			log.Info("Received shutdown signal")
			cancel()
			return

		case <-updater.updateChan:
			if err := updater.performUpdate(ctx); err != nil {
				log.WithError(err).Error("Failed to update threats")
			}
			
			// Schedule next update
			go func() {
				time.Sleep(5 * time.Minute) // Update every 5 minutes
				select {
				case updater.updateChan <- struct{}{}:
				default:
					// Channel full, skip this update
				}
			}()

		case <-time.After(1 * time.Hour):
			// Cleanup old threats periodically
			if err := updater.cleanupOldThreats(ctx); err != nil {
				log.WithError(err).Error("Failed to cleanup old threats")
			}
		}
	}
}

// performUpdate fetches and updates threat intelligence
func (tu *ThreatUpdater) performUpdate(ctx context.Context) error {
	tu.logger.Info("Starting threat intelligence update")
	startTime := time.Now()

	var allEntries []feeds.ThreatEntry

	// Fetch threat intelligence feeds
	threatEntries, err := tu.feedManager.UpdateAllFeeds(ctx)
	if err != nil {
		tu.logger.WithError(err).Warn("Failed to update threat feeds")
	} else {
		allEntries = append(allEntries, threatEntries...)
		tu.logger.WithField("threat_entries", len(threatEntries)).Info("Updated threat intelligence feeds")
	}

	// Fetch ad blocking feeds
	adEntries, err := tu.adBlockManager.UpdateAllAdBlockFeeds(ctx)
	if err != nil {
		tu.logger.WithError(err).Warn("Failed to update ad blocking feeds")
	} else {
		allEntries = append(allEntries, adEntries...)
		tu.logger.WithField("ad_entries", len(adEntries)).Info("Updated ad blocking feeds")
	}

	if len(allEntries) == 0 {
		tu.logger.Info("No new entries to process")
		return nil
	}

	// Batch insert into database
	if err := tu.threatDB.BatchInsertThreats(ctx, allEntries); err != nil {
		return fmt.Errorf("inserting threats: %w", err)
	}

	// Get updated statistics
	stats, err := tu.threatDB.GetThreatStats(ctx)
	if err != nil {
		tu.logger.WithError(err).Warn("Failed to get threat statistics")
	} else {
		tu.logger.WithFields(logrus.Fields{
			"stats":        stats,
			"duration":     time.Since(startTime),
			"new_entries":  len(allEntries),
			"threat_feeds": len(threatEntries),
			"ad_feeds":     len(adEntries),
		}).Info("Successfully updated threat intelligence and ad blocking")
	}

	return nil
}

// cleanupOldThreats removes outdated threat entries
func (tu *ThreatUpdater) cleanupOldThreats(ctx context.Context) error {
	tu.logger.Info("Starting threat cleanup")
	
	// Remove threats older than 30 days
	maxAge := 30 * 24 * time.Hour
	
	return tu.threatDB.CleanupOldThreats(ctx, maxAge)
}