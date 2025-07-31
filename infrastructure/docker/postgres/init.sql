-- GuardNet Database Initialization
-- Create database schema and initial tables

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Routers table
CREATE TABLE routers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_mac VARCHAR(17) UNIQUE NOT NULL,
    router_model VARCHAR(100),
    dns_config JSONB,
    is_active BOOLEAN DEFAULT true,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Threat intelligence table
CREATE TABLE threat_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    threat_type VARCHAR(50) NOT NULL, -- malware, phishing, ads, etc.
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- DNS query logs
CREATE TABLE dns_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    router_id UUID REFERENCES routers(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    query_type VARCHAR(10), -- A, AAAA, CNAME, etc.
    response_type VARCHAR(20), -- allowed, blocked, redirected
    threat_type VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscription plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    price_monthly DECIMAL(10,2),
    features JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES subscription_plans(id),
    status VARCHAR(20) DEFAULT 'active', -- active, cancelled, expired
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ad revenue tracking
CREATE TABLE ad_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ad_network VARCHAR(100),
    revenue_amount DECIMAL(10,4),
    user_share DECIMAL(10,4),
    date_earned DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_routers_user_id ON routers(user_id);
CREATE INDEX idx_dns_logs_router_id ON dns_logs(router_id);
CREATE INDEX idx_dns_logs_timestamp ON dns_logs(timestamp);
CREATE INDEX idx_threat_domains_domain ON threat_domains(domain);
CREATE INDEX idx_threat_domains_type ON threat_domains(threat_type);

-- Insert initial subscription plans
INSERT INTO subscription_plans (name, price_monthly, features) VALUES
('Basic', 9.99, '{"dns_filtering": true, "basic_threats": true, "devices": 5}'),
('Pro', 19.99, '{"dns_filtering": true, "ai_threats": true, "vpn": true, "devices": 15, "parental_controls": true}'),
('Family', 29.99, '{"dns_filtering": true, "ai_threats": true, "vpn": true, "devices": 50, "parental_controls": true, "ad_blocking": true}');

-- Enhanced threat domains with more real-world examples
INSERT INTO threat_domains (domain, threat_type, confidence_score, source) VALUES
('malware-test.com', 'malware', 0.95, 'urlhaus'),
('phishing-example.org', 'phishing', 0.98, 'openphish'),
('doubleclick.net', 'ads', 0.90, 'easylist'),
('googleadservices.com', 'ads', 0.85, 'easylist'),
('googlesyndication.com', 'ads', 0.85, 'easylist'),
('facebook.com', 'ads', 0.80, 'manual'),
('ads.yahoo.com', 'ads', 0.88, 'easylist'),
('amazon-adsystem.com', 'ads', 0.87, 'easylist');