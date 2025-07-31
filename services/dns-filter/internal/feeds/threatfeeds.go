package feeds

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

// ThreatFeed represents a threat intelligence feed
type ThreatFeed struct {
	Name         string        `json:"name"`
	URL          string        `json:"url"`
	Type         string        `json:"type"` // json, csv, txt
	UpdateFreq   time.Duration `json:"update_frequency"`
	LastUpdated  time.Time     `json:"last_updated"`
	IsEnabled    bool          `json:"is_enabled"`
	RequiresAuth bool          `json:"requires_auth"`
}

// ThreatEntry represents a single threat domain entry
type ThreatEntry struct {
	Domain         string            `json:"domain"`
	ThreatType     string            `json:"threat_type"`
	Confidence     float64           `json:"confidence"`
	Source         string            `json:"source"`
	FirstSeen      time.Time         `json:"first_seen"`
	LastSeen       time.Time         `json:"last_seen"`
	IsActive       bool              `json:"is_active"`
	Metadata       map[string]string `json:"metadata"`
}

// URLhausEntry represents URLhaus JSON format
type URLhausEntry struct {
	ID           string    `json:"id"`
	URL          string    `json:"url"`
	URLStatus    string    `json:"url_status"`
	Host         string    `json:"host"`
	DateAdded    time.Time `json:"date_added"`
	ThreatType   string    `json:"threat"`
	Tags         []string  `json:"tags"`
	PayloadType  string    `json:"payload_type"`
}

// PhishTankEntry represents PhishTank JSON format
type PhishTankEntry struct {
	PhishID      int    `json:"phish_id"`
	URL          string `json:"url"`
	PhishDetail  string `json:"phish_detail_url"`
	Submission   string `json:"submission_time"`
	Verified     string `json:"verified"`
	VerifiedTime string `json:"verification_time"`
	Online       string `json:"online"`
	Target       string `json:"target"`
}

// FeedManager manages threat intelligence feeds
type FeedManager struct {
	feeds  []ThreatFeed
	client *http.Client
	logger *logrus.Logger
}

// NewFeedManager creates a new feed manager
func NewFeedManager(logger *logrus.Logger) *FeedManager {
	return &FeedManager{
		feeds: []ThreatFeed{
			{
				Name:       "URLhaus",
				URL:        "https://urlhaus.abuse.ch/downloads/json/",
				Type:       "json",
				UpdateFreq: 5 * time.Minute,
				IsEnabled:  true,
			},
			{
				Name:       "OpenPhish",
				URL:        "https://openphish.com/feed.txt",
				Type:       "txt",
				UpdateFreq: 30 * time.Minute,
				IsEnabled:  true,
			},
			{
				Name:       "PhishTank",
				URL:        "http://data.phishtank.com/data/online-valid.json",
				Type:       "json",
				UpdateFreq: 60 * time.Minute,
				IsEnabled:  false, // Requires registration
			},
		},
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		logger: logger,
	}
}

// UpdateAllFeeds updates all enabled threat feeds
func (fm *FeedManager) UpdateAllFeeds(ctx context.Context) ([]ThreatEntry, error) {
	var allEntries []ThreatEntry

	for _, feed := range fm.feeds {
		if !feed.IsEnabled {
			continue
		}

		// Check if update is needed
		if time.Since(feed.LastUpdated) < feed.UpdateFreq {
			fm.logger.WithField("feed", feed.Name).Debug("Feed update not needed yet")
			continue
		}

		fm.logger.WithField("feed", feed.Name).Info("Updating threat feed")
		
		entries, err := fm.updateFeed(ctx, feed)
		if err != nil {
			fm.logger.WithError(err).WithField("feed", feed.Name).Error("Failed to update feed")
			continue
		}

		allEntries = append(allEntries, entries...)
		feed.LastUpdated = time.Now()
		
		fm.logger.WithFields(logrus.Fields{
			"feed":    feed.Name,
			"entries": len(entries),
		}).Info("Successfully updated threat feed")
	}

	return allEntries, nil
}

// updateFeed updates a specific feed
func (fm *FeedManager) updateFeed(ctx context.Context, feed ThreatFeed) ([]ThreatEntry, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", feed.URL, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	req.Header.Set("User-Agent", "GuardNet-DNS-Filter/1.0")

	resp, err := fm.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetching feed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, resp.Status)
	}

	switch feed.Type {
	case "json":
		return fm.parseJSONFeed(resp.Body, feed)
	case "txt":
		return fm.parseTextFeed(resp.Body, feed)
	default:
		return nil, fmt.Errorf("unsupported feed type: %s", feed.Type)
	}
}

// parseJSONFeed parses JSON threat feeds
func (fm *FeedManager) parseJSONFeed(body io.Reader, feed ThreatFeed) ([]ThreatEntry, error) {
	var entries []ThreatEntry

	switch feed.Name {
	case "URLhaus":
		var urlhausData []URLhausEntry
		if err := json.NewDecoder(body).Decode(&urlhausData); err != nil {
			return nil, fmt.Errorf("parsing URLhaus JSON: %w", err)
		}

		for _, item := range urlhausData {
			if item.URLStatus != "online" {
				continue
			}

			domain := extractDomain(item.Host)
			if domain == "" {
				continue
			}

			threatType := "malware"
			if strings.Contains(strings.ToLower(item.ThreatType), "phish") {
				threatType = "phishing"
			}

			entries = append(entries, ThreatEntry{
				Domain:     domain,
				ThreatType: threatType,
				Confidence: 0.90, // URLhaus is high confidence
				Source:     "urlhaus",
				FirstSeen:  item.DateAdded,
				LastSeen:   time.Now(),
				IsActive:   true,
				Metadata: map[string]string{
					"payload_type": item.PayloadType,
					"tags":        strings.Join(item.Tags, ","),
					"url_id":      item.ID,
				},
			})
		}

	case "PhishTank":
		var phishData []PhishTankEntry
		if err := json.NewDecoder(body).Decode(&phishData); err != nil {
			return nil, fmt.Errorf("parsing PhishTank JSON: %w", err)
		}

		for _, item := range phishData {
			if item.Online != "yes" || item.Verified != "yes" {
				continue
			}

			domain := extractDomain(item.URL)
			if domain == "" {
				continue
			}

			entries = append(entries, ThreatEntry{
				Domain:     domain,
				ThreatType: "phishing",
				Confidence: 0.95, // PhishTank is verified data
				Source:     "phishtank",
				FirstSeen:  time.Now(),
				LastSeen:   time.Now(),
				IsActive:   true,
				Metadata: map[string]string{
					"target":   item.Target,
					"phish_id": fmt.Sprintf("%d", item.PhishID),
				},
			})
		}
	}

	return entries, nil
}

// parseTextFeed parses text-based threat feeds
func (fm *FeedManager) parseTextFeed(body io.Reader, feed ThreatFeed) ([]ThreatEntry, error) {
	var entries []ThreatEntry
	scanner := bufio.NewScanner(body)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		var domain string
		var threatType string

		switch feed.Name {
		case "OpenPhish":
			// OpenPhish provides full URLs
			domain = extractDomain(line)
			threatType = "phishing"
		default:
			// Assume it's a domain list
			domain = line
			threatType = "malware"
		}

		if domain == "" || !isValidDomain(domain) {
			continue
		}

		entries = append(entries, ThreatEntry{
			Domain:     domain,
			ThreatType: threatType,
			Confidence: 0.85, // Text feeds are generally lower confidence
			Source:     strings.ToLower(feed.Name),
			FirstSeen:  time.Now(),
			LastSeen:   time.Now(),
			IsActive:   true,
			Metadata:   map[string]string{},
		})
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("reading feed: %w", err)
	}

	return entries, nil
}

// extractDomain extracts domain from URL
func extractDomain(rawURL string) string {
	if rawURL == "" {
		return ""
	}

	// If it doesn't start with http(s), assume it's already a host
	if !strings.HasPrefix(rawURL, "http") {
		rawURL = "http://" + rawURL
	}

	parsedURL, err := url.Parse(rawURL)
	if err != nil {
		return ""
	}

	host := parsedURL.Host
	// Remove port if present
	if colonIndex := strings.LastIndex(host, ":"); colonIndex > strings.LastIndex(host, "]") {
		host = host[:colonIndex]
	}

	return strings.ToLower(host)
}

// isValidDomain validates domain format
func isValidDomain(domain string) bool {
	if len(domain) == 0 || len(domain) > 255 {
		return false
	}

	// Basic domain validation regex
	domainRegex := regexp.MustCompile(`^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$`)
	return domainRegex.MatchString(domain)
}