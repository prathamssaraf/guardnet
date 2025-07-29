package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Collector holds all metrics for the DNS filtering service
type Collector struct {
	// DNS query metrics
	DNSQueriesTotal   prometheus.Counter
	DNSBlocked        prometheus.Counter
	DNSAllowed        prometheus.Counter
	DNSErrors         prometheus.Counter
	DNSResponseTime   prometheus.Histogram
	DNSQueriesByType  *prometheus.CounterVec
	
	// Threat detection metrics
	ThreatsByType     *prometheus.CounterVec
	CacheHits         prometheus.Counter
	CacheMisses       prometheus.Counter
	
	// System metrics
	ActiveConnections prometheus.Gauge
	DatabaseQueries   prometheus.Counter
	DatabaseErrors    prometheus.Counter
	
	// Rate limiting metrics
	RateLimitHits     prometheus.Counter
	BlockedIPs        prometheus.Gauge
}

// NewCollector creates a new metrics collector with all DNS filtering metrics
func NewCollector() *Collector {
	return &Collector{
		// DNS query counters
		DNSQueriesTotal: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_dns_queries_total",
			Help: "Total number of DNS queries processed",
		}),
		
		DNSBlocked: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_dns_blocked_total",
			Help: "Total number of DNS queries blocked",
		}),
		
		DNSAllowed: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_dns_allowed_total", 
			Help: "Total number of DNS queries allowed",
		}),
		
		DNSErrors: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_dns_errors_total",
			Help: "Total number of DNS query errors",
		}),
		
		// DNS response time histogram
		DNSResponseTime: promauto.NewHistogram(prometheus.HistogramOpts{
			Name:    "guardnet_dns_response_time_seconds",
			Help:    "DNS query response time in seconds",
			Buckets: prometheus.DefBuckets,
		}),
		
		// DNS queries by type (A, AAAA, CNAME, etc.)
		DNSQueriesByType: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "guardnet_dns_queries_by_type_total",
				Help: "Total DNS queries by query type",
			},
			[]string{"query_type"},
		),
		
		// Threat detection metrics
		ThreatsByType: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "guardnet_threats_by_type_total",
				Help: "Total threats detected by threat type",
			},
			[]string{"threat_type"},
		),
		
		// Cache performance
		CacheHits: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_cache_hits_total",
			Help: "Total number of cache hits",
		}),
		
		CacheMisses: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_cache_misses_total",
			Help: "Total number of cache misses",
		}),
		
		// System metrics
		ActiveConnections: promauto.NewGauge(prometheus.GaugeOpts{
			Name: "guardnet_active_connections",
			Help: "Number of active DNS connections",
		}),
		
		DatabaseQueries: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_database_queries_total",
			Help: "Total number of database queries",
		}),
		
		DatabaseErrors: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_database_errors_total",
			Help: "Total number of database errors",
		}),
		
		// Rate limiting
		RateLimitHits: promauto.NewCounter(prometheus.CounterOpts{
			Name: "guardnet_rate_limit_hits_total",
			Help: "Total number of rate limit violations",
		}),
		
		BlockedIPs: promauto.NewGauge(prometheus.GaugeOpts{
			Name: "guardnet_blocked_ips",
			Help: "Number of currently blocked IP addresses",
		}),
	}
}

// RecordDNSQuery records metrics for a DNS query
func (c *Collector) RecordDNSQuery(queryType string, responseTime float64, blocked bool, threatType string) {
	// Increment total queries
	c.DNSQueriesTotal.Inc()
	
	// Record query type
	c.DNSQueriesByType.WithLabelValues(queryType).Inc()
	
	// Record response time
	c.DNSResponseTime.Observe(responseTime)
	
	// Record result
	if blocked {
		c.DNSBlocked.Inc()
		if threatType != "" {
			c.ThreatsByType.WithLabelValues(threatType).Inc()
		}
	} else {
		c.DNSAllowed.Inc()
	}
}

// RecordCacheHit records a cache hit
func (c *Collector) RecordCacheHit() {
	c.CacheHits.Inc()
}

// RecordCacheMiss records a cache miss
func (c *Collector) RecordCacheMiss() {
	c.CacheMisses.Inc()
}

// RecordDatabaseQuery records a database query
func (c *Collector) RecordDatabaseQuery() {
	c.DatabaseQueries.Inc()
}

// RecordDatabaseError records a database error
func (c *Collector) RecordDatabaseError() {
	c.DatabaseErrors.Inc()
}

// RecordRateLimitHit records a rate limit violation
func (c *Collector) RecordRateLimitHit() {
	c.RateLimitHits.Inc()
}

// SetActiveConnections sets the number of active connections
func (c *Collector) SetActiveConnections(count float64) {
	c.ActiveConnections.Set(count)
}

// SetBlockedIPs sets the number of blocked IP addresses
func (c *Collector) SetBlockedIPs(count float64) {
	c.BlockedIPs.Set(count)
}

// GetCacheHitRatio returns the cache hit ratio
func (c *Collector) GetCacheHitRatio() float64 {
	hits := c.getCacheHitsCount()
	misses := c.getCacheMissesCount()
	
	total := hits + misses
	if total == 0 {
		return 0
	}
	
	return hits / total
}

// Helper method to get cache hits count
func (c *Collector) getCacheHitsCount() float64 {
	metric := &prometheus.Metric{}
	c.CacheHits.Write(metric)
	return metric.GetCounter().GetValue()
}

// Helper method to get cache misses count  
func (c *Collector) getCacheMissesCount() float64 {
	metric := &prometheus.Metric{}
	c.CacheMisses.Write(metric)
	return metric.GetCounter().GetValue()
}