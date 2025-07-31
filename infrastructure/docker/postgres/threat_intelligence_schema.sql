-- GuardNet Threat Intelligence Database Schema
-- Designed for real-time DNS filtering with multiple threat feed sources

-- Main threat domains table
CREATE TABLE IF NOT EXISTS threat_domains (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    threat_type VARCHAR(50) NOT NULL, -- malware, phishing, ads, spam, botnet
    confidence_score INTEGER DEFAULT 50 CHECK (confidence_score >= 0 AND confidence_score <= 100),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100) NOT NULL, -- urlhaus, openphish, spamhaus, etc.
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}', -- Additional threat intel data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Threat feed sources tracking
CREATE TABLE IF NOT EXISTS threat_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    url VARCHAR(500),
    feed_type VARCHAR(50), -- api, csv, json, rss
    update_frequency INTEGER DEFAULT 300, -- seconds
    last_updated TIMESTAMP,
    is_enabled BOOLEAN DEFAULT true,
    api_key_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DNS query logs for analytics
CREATE TABLE IF NOT EXISTS dns_queries (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    client_ip INET,
    query_type VARCHAR(10), -- A, AAAA, MX, etc.
    response_type VARCHAR(20), -- blocked, allowed, cached
    threat_type VARCHAR(50), -- if blocked
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent VARCHAR(255),
    country_code CHAR(2)
);

-- Machine learning features for domain analysis
CREATE TABLE IF NOT EXISTS domain_features (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    domain_length INTEGER,
    subdomain_count INTEGER,
    has_numbers BOOLEAN,
    has_hyphens BOOLEAN,
    entropy_score DECIMAL(5,4),
    tld VARCHAR(50),
    domain_age_days INTEGER,
    registrar VARCHAR(255),
    ml_score DECIMAL(5,4), -- 0.0 = safe, 1.0 = malicious
    features_json JSONB,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User feedback for continuous learning
CREATE TABLE IF NOT EXISTS user_feedback (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    user_id VARCHAR(100),
    feedback_type VARCHAR(20), -- false_positive, false_negative, correct
    original_classification VARCHAR(50),
    user_classification VARCHAR(50),
    confidence INTEGER CHECK (confidence >= 1 AND confidence <= 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_threat_domains_domain ON threat_domains(domain);
CREATE INDEX IF NOT EXISTS idx_threat_domains_type ON threat_domains(threat_type);
CREATE INDEX IF NOT EXISTS idx_threat_domains_active ON threat_domains(is_active);
CREATE INDEX IF NOT EXISTS idx_threat_domains_source ON threat_domains(source);
CREATE INDEX IF NOT EXISTS idx_threat_domains_updated ON threat_domains(updated_at);

CREATE INDEX IF NOT EXISTS idx_dns_queries_domain ON dns_queries(domain);
CREATE INDEX IF NOT EXISTS idx_dns_queries_timestamp ON dns_queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_dns_queries_response_type ON dns_queries(response_type);

CREATE INDEX IF NOT EXISTS idx_domain_features_domain ON domain_features(domain);
CREATE INDEX IF NOT EXISTS idx_domain_features_ml_score ON domain_features(ml_score);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_threat_domains_updated_at 
    BEFORE UPDATE ON threat_domains 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default threat sources
INSERT INTO threat_sources (name, url, feed_type, update_frequency) VALUES
('URLhaus', 'https://urlhaus.abuse.ch/downloads/json/', 'json', 300),
('OpenPhish', 'https://openphish.com/feed.txt', 'txt', 1800),
('Spamhaus DBL', 'https://www.spamhaus.org/dbl/', 'api', 3600),
('PhishTank', 'https://data.phishtank.com/data/online-valid.json', 'json', 3600),
('MalwareDomains', 'https://mirror1.malwaredomains.com/files/domains.txt', 'txt', 7200)
ON CONFLICT (name) DO NOTHING;

-- Sample data for testing
INSERT INTO threat_domains (domain, threat_type, confidence_score, source, metadata) VALUES
('malware-test.com', 'malware', 95, 'urlhaus', '{"campaign": "test_malware", "family": "generic"}'),
('phishing-example.org', 'phishing', 90, 'openphish', '{"target": "banking", "brand": "generic"}'),
('ads.tracker.com', 'ads', 80, 'manual', '{"category": "tracking", "privacy_risk": "high"}'),
('spam.example.net', 'spam', 85, 'spamhaus', '{"type": "email_spam", "volume": "high"}'),
('botnet.evil.io', 'botnet', 98, 'urlhaus', '{"botnet_family": "emotet", "c2_server": true}')
ON CONFLICT (domain) DO NOTHING;