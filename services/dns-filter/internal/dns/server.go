package dns

import (
	"context"
	"fmt"
	"net"
	"strings"
	"sync"
	"time"

	"guardnet/dns-filter/internal/cache"
	"guardnet/dns-filter/internal/db"
	"guardnet/dns-filter/internal/metrics"
	"guardnet/dns-filter/pkg/logger"

	"github.com/miekg/dns"
)

// Server represents the DNS filtering server
type Server struct {
	address    string
	server     *dns.Server
	database   *db.Connection
	cache      *cache.RedisClient
	metrics    *metrics.Collector
	logger     *logger.Logger
	upstreams  []string
	ready      bool
	readyMutex sync.RWMutex
}

// Config holds configuration for the DNS server
type Config struct {
	Address    string
	Database   *db.Connection
	Cache      *cache.RedisClient
	Metrics    *metrics.Collector
	Logger     *logger.Logger
	Upstreams  []string
}

// NewServer creates a new DNS server instance
func NewServer(cfg *Config) *Server {
	upstreams := cfg.Upstreams
	if len(upstreams) == 0 {
		upstreams = []string{"1.1.1.1:53", "8.8.8.8:53"}
	}

	return &Server{
		address:   cfg.Address,
		database:  cfg.Database,
		cache:     cfg.Cache,
		metrics:   cfg.Metrics,
		logger:    cfg.Logger,
		upstreams: upstreams,
		ready:     false,
	}
}

// Start starts the DNS server
func (s *Server) Start() error {
	mux := dns.NewServeMux()
	mux.HandleFunc(".", s.handleDNSRequest)

	s.server = &dns.Server{
		Addr:    s.address,
		Net:     "udp",
		Handler: mux,
	}

	s.setReady(true)
	s.logger.Info("DNS server listening", "address", s.address)
	
	return s.server.ListenAndServe()
}

// Shutdown gracefully shuts down the DNS server
func (s *Server) Shutdown(ctx context.Context) error {
	s.setReady(false)
	if s.server != nil {
		return s.server.ShutdownContext(ctx)
	}
	return nil
}

// IsReady returns whether the server is ready to serve requests
func (s *Server) IsReady() bool {
	s.readyMutex.RLock()
	defer s.readyMutex.RUnlock()
	return s.ready
}

// setReady sets the ready state
func (s *Server) setReady(ready bool) {
	s.readyMutex.Lock()
	defer s.readyMutex.Unlock()
	s.ready = ready
}

// handleDNSRequest handles incoming DNS requests
func (s *Server) handleDNSRequest(w dns.ResponseWriter, r *dns.Msg) {
	start := time.Now()
	
	// Increment request counter
	s.metrics.DNSQueriesTotal.Inc()
	
	// Get client IP
	clientIP := s.getClientIP(w)
	
	// Create response message
	msg := dns.Msg{}
	msg.SetReply(r)
	msg.Authoritative = false
	msg.RecursionAvailable = true

	// Process each question in the request
	for _, question := range r.Question {
		domain := strings.ToLower(strings.TrimSuffix(question.Name, "."))
		
		s.logger.Debug("Processing DNS query", 
			"domain", domain, 
			"type", dns.TypeToString[question.Qtype],
			"client", clientIP)

		// Check if domain should be blocked
		blocked, threatType, err := s.shouldBlockDomain(domain)
		if err != nil {
			s.logger.Error("Error checking domain", "domain", domain, "error", err)
			s.metrics.DNSErrors.Inc()
			// Continue with normal resolution on error
		}

		if blocked {
			s.logger.Info("Blocked domain", "domain", domain, "threat_type", threatType, "client", clientIP)
			s.metrics.DNSBlocked.Inc()
			
			// Log the blocked query
			s.logDNSQuery(clientIP, domain, dns.TypeToString[question.Qtype], "blocked", threatType)
			
			// Return NXDOMAIN for blocked domains
			msg.Rcode = dns.RcodeNameError
			break
		}

		// Forward to upstream DNS
		answer, err := s.forwardToUpstream(question, domain)
		if err != nil {
			s.logger.Error("Failed to forward DNS query", "domain", domain, "error", err)
			s.metrics.DNSErrors.Inc()
			msg.Rcode = dns.RcodeServerFailure
			break
		}

		if answer != nil {
			msg.Answer = append(msg.Answer, answer...)
			s.metrics.DNSAllowed.Inc()
			
			// Log the allowed query
			s.logDNSQuery(clientIP, domain, dns.TypeToString[question.Qtype], "allowed", "")
		}
	}

	// Record response time
	duration := time.Since(start)
	s.metrics.DNSResponseTime.Observe(duration.Seconds())

	// Send response
	if err := w.WriteMsg(&msg); err != nil {
		s.logger.Error("Failed to write DNS response", "error", err)
		s.metrics.DNSErrors.Inc()
	}
}

// shouldBlockDomain checks if a domain should be blocked
func (s *Server) shouldBlockDomain(domain string) (bool, string, error) {
	// Check cache first
	cacheKey := fmt.Sprintf("domain:%s", domain)
	if cached, err := s.cache.Get(cacheKey); err == nil && cached != "" {
		if cached == "blocked" {
			return true, "cached", nil
		}
		if cached == "allowed" {
			return false, "", nil
		}
	}

	// Check against threat database
	threatType, err := s.database.CheckThreatDomain(domain)
	if err != nil {
		return false, "", err
	}

	if threatType != "" {
		// Cache as blocked for 1 hour
		s.cache.Set(cacheKey, "blocked", time.Hour)
		return true, threatType, nil
	}

	// Check parent domains (for subdomains)
	parts := strings.Split(domain, ".")
	for i := 1; i < len(parts); i++ {
		parentDomain := strings.Join(parts[i:], ".")
		parentThreatType, err := s.database.CheckThreatDomain(parentDomain)
		if err != nil {
			continue
		}
		if parentThreatType != "" {
			// Cache as blocked for 1 hour
			s.cache.Set(cacheKey, "blocked", time.Hour)
			return true, parentThreatType, nil
		}
	}

	// Cache as allowed for 30 minutes
	s.cache.Set(cacheKey, "allowed", 30*time.Minute)
	return false, "", nil
}

// forwardToUpstream forwards DNS query to upstream servers
func (s *Server) forwardToUpstream(question dns.Question, domain string) ([]dns.RR, error) {
	msg := &dns.Msg{}
	msg.SetQuestion(dns.Fqdn(domain), question.Qtype)
	msg.RecursionDesired = true

	// Try each upstream server
	for _, upstream := range s.upstreams {
		client := &dns.Client{
			Timeout: 5 * time.Second,
		}

		response, _, err := client.Exchange(msg, upstream)
		if err != nil {
			s.logger.Debug("Upstream DNS failed", "upstream", upstream, "error", err)
			continue
		}

		if response.Rcode == dns.RcodeSuccess && len(response.Answer) > 0 {
			return response.Answer, nil
		}

		// If we get NXDOMAIN, return it immediately
		if response.Rcode == dns.RcodeNameError {
			return nil, nil
		}
	}

	return nil, fmt.Errorf("all upstream servers failed")
}

// getClientIP extracts client IP from DNS request
func (s *Server) getClientIP(w dns.ResponseWriter) string {
	if addr := w.RemoteAddr(); addr != nil {
		if udpAddr, ok := addr.(*net.UDPAddr); ok {
			return udpAddr.IP.String()
		}
		if tcpAddr, ok := addr.(*net.TCPAddr); ok {
			return tcpAddr.IP.String()
		}
	}
	return "unknown"
}

// logDNSQuery logs DNS query to database (async)
func (s *Server) logDNSQuery(clientIP, domain, queryType, responseType, threatType string) {
	go func() {
		if err := s.database.LogDNSQuery(clientIP, domain, queryType, responseType, threatType); err != nil {
			s.logger.Error("Failed to log DNS query", "error", err)
		}
	}()
}