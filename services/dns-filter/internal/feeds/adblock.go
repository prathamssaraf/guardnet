package feeds

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

// AdBlockFeed represents an ad blocking feed source
type AdBlockFeed struct {
	Name         string        `json:"name"`
	URL          string        `json:"url"`
	Format       string        `json:"format"` // hosts, easylist, domains
	UpdateFreq   time.Duration `json:"update_frequency"`
	LastUpdated  time.Time     `json:"last_updated"`
	IsEnabled    bool          `json:"is_enabled"`
	Description  string        `json:"description"`
}

// AdBlockManager manages ad blocking lists
type AdBlockManager struct {
	feeds  []AdBlockFeed
	client *http.Client
	logger *logrus.Logger
}

// NewAdBlockManager creates a new ad block manager
func NewAdBlockManager(logger *logrus.Logger) *AdBlockManager {
	return &AdBlockManager{
		feeds: []AdBlockFeed{
			{
				Name:        "EasyList",
				URL:         "https://easylist.to/easylist/easylist.txt",
				Format:      "easylist",
				UpdateFreq:  24 * time.Hour,
				IsEnabled:   true,
				Description: "Primary ad blocking list",
			},
			{
				Name:        "EasyPrivacy",
				URL:         "https://easylist.to/easylist/easyprivacy.txt",
				Format:      "easylist",
				UpdateFreq:  24 * time.Hour,
				IsEnabled:   true,
				Description: "Privacy protection list",
			},
			{
				Name:        "AdGuard Base",
				URL:         "https://filters.adtidy.org/extension/chromium/filters/2.txt",
				Format:      "easylist",
				UpdateFreq:  12 * time.Hour,
				IsEnabled:   true,
				Description: "AdGuard base filter",
			},
			{
				Name:        "StevenBlack Hosts",
				URL:         "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
				Format:      "hosts",
				UpdateFreq:  24 * time.Hour,
				IsEnabled:   true,
				Description: "Unified hosts file with ads and malware",
			},
			{
				Name:        "Peter Lowe's List",
				URL:         "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext",
				Format:      "hosts",
				UpdateFreq:  24 * time.Hour,
				IsEnabled:   true,
				Description: "Personal ad server list",
			},
			{
				Name:        "Dan Pollock's Hosts",
				URL:         "https://someonewhocares.org/hosts/zero/hosts",
				Format:      "hosts",
				UpdateFreq:  24 * time.Hour,
				IsEnabled:   true,
				Description: "Comprehensive ad and malware hosts",
			},
		},
		client: &http.Client{
			Timeout: 60 * time.Second,
		},
		logger: logger,
	}
}

// UpdateAllAdBlockFeeds updates all enabled ad blocking feeds
func (abm *AdBlockManager) UpdateAllAdBlockFeeds(ctx context.Context) ([]ThreatEntry, error) {
	var allEntries []ThreatEntry

	for _, feed := range abm.feeds {
		if !feed.IsEnabled {
			continue
		}

		// Check if update is needed
		if time.Since(feed.LastUpdated) < feed.UpdateFreq {
			abm.logger.WithField("feed", feed.Name).Debug("Ad block feed update not needed yet")
			continue
		}

		abm.logger.WithField("feed", feed.Name).Info("Updating ad blocking feed")

		entries, err := abm.updateAdBlockFeed(ctx, feed)
		if err != nil {
			abm.logger.WithError(err).WithField("feed", feed.Name).Error("Failed to update ad block feed")
			continue
		}

		allEntries = append(allEntries, entries...)
		feed.LastUpdated = time.Now()

		abm.logger.WithFields(logrus.Fields{
			"feed":    feed.Name,
			"entries": len(entries),
		}).Info("Successfully updated ad blocking feed")
	}

	return allEntries, nil
}

// updateAdBlockFeed updates a specific ad blocking feed
func (abm *AdBlockManager) updateAdBlockFeed(ctx context.Context, feed AdBlockFeed) ([]ThreatEntry, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", feed.URL, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	req.Header.Set("User-Agent", "GuardNet-DNS-Filter/1.0")

	resp, err := abm.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetching feed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, resp.Status)
	}

	switch feed.Format {
	case "hosts":
		return abm.parseHostsFormat(resp.Body, feed)
	case "easylist":
		return abm.parseEasyListFormat(resp.Body, feed)
	case "domains":
		return abm.parseDomainsFormat(resp.Body, feed)
	default:
		return nil, fmt.Errorf("unsupported feed format: %s", feed.Format)
	}
}

// parseHostsFormat parses hosts file format (127.0.0.1 domain.com)
func (abm *AdBlockManager) parseHostsFormat(body io.Reader, feed AdBlockFeed) ([]ThreatEntry, error) {
	var entries []ThreatEntry
	scanner := bufio.NewScanner(body)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Parse hosts format: IP domain
		parts := strings.Fields(line)
		if len(parts) < 2 {
			continue
		}

		domain := strings.ToLower(parts[1])
		if !isValidDomain(domain) || domain == "localhost" || strings.Contains(domain, "localhost") {
			continue
		}

		entries = append(entries, ThreatEntry{
			Domain:     domain,
			ThreatType: "ads",
			Confidence: 0.85,
			Source:     strings.ToLower(strings.Replace(feed.Name, " ", "_", -1)),
			FirstSeen:  time.Now(),
			LastSeen:   time.Now(),
			IsActive:   true,
			Metadata: map[string]string{
				"feed_format": "hosts",
				"category":    "advertising",
			},
		})

		// Limit entries to prevent memory issues
		if len(entries) >= 50000 {
			break
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("reading hosts feed: %w", err)
	}

	return entries, nil
}

// parseEasyListFormat parses EasyList/AdBlock Plus format
func (abm *AdBlockManager) parseEasyListFormat(body io.Reader, feed AdBlockFeed) ([]ThreatEntry, error) {
	var entries []ThreatEntry
	scanner := bufio.NewScanner(body)

	// Regex patterns for different EasyList rules
	domainPattern := regexp.MustCompile(`^\|\|([a-zA-Z0-9.-]+)\^`)
	urlPattern := regexp.MustCompile(`^\|\|([a-zA-Z0-9.-]+)/`)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "!") || strings.HasPrefix(line, "[") {
			continue
		}

		var domain string

		// Check for domain blocking rules (||domain.com^)
		if matches := domainPattern.FindStringSubmatch(line); len(matches) > 1 {
			domain = strings.ToLower(matches[1])
		} else if matches := urlPattern.FindStringSubmatch(line); len(matches) > 1 {
			domain = strings.ToLower(matches[1])
		}

		if domain != "" && isValidDomain(domain) {
			entries = append(entries, ThreatEntry{
				Domain:     domain,
				ThreatType: "ads",
				Confidence: 0.80,
				Source:     strings.ToLower(strings.Replace(feed.Name, " ", "_", -1)),
				FirstSeen:  time.Now(),
				LastSeen:   time.Now(),
				IsActive:   true,
				Metadata: map[string]string{
					"feed_format": "easylist",
					"rule_type":   "domain_block",
				},
			})

			// Limit entries to prevent memory issues
			if len(entries) >= 30000 {
				break
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("reading easylist feed: %w", err)
	}

	return entries, nil
}

// parseDomainsFormat parses simple domain list format
func (abm *AdBlockManager) parseDomainsFormat(body io.Reader, feed AdBlockFeed) ([]ThreatEntry, error) {
	var entries []ThreatEntry
	scanner := bufio.NewScanner(body)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		domain := strings.ToLower(line)
		if !isValidDomain(domain) {
			continue
		}

		entries = append(entries, ThreatEntry{
			Domain:     domain,
			ThreatType: "ads",
			Confidence: 0.85,
			Source:     strings.ToLower(strings.Replace(feed.Name, " ", "_", -1)),
			FirstSeen:  time.Now(),
			LastSeen:   time.Now(),
			IsActive:   true,
			Metadata: map[string]string{
				"feed_format": "domains",
				"category":    "advertising",
			},
		})

		// Limit entries to prevent memory issues
		if len(entries) >= 50000 {
			break
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("reading domains feed: %w", err)
	}

	return entries, nil
}