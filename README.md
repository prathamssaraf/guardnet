# GuardNet - Intelligent DNS Security Platform

Enterprise-grade network protection through intelligent DNS filtering, ad blocking, and threat intelligence.

## 🛡️ Features

- **DNS Filtering**: Block malware, phishing, and malicious domains
- **Ad Blocking**: Remove ads and trackers for faster browsing
- **Threat Intelligence**: Real-time threat feed integration
- **Router Integration**: Network-wide protection via DNS
- **Family Protection**: Safe browsing for all connected devices
- **Performance Optimization**: Fast response times with intelligent caching

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Internet      │────│   GuardNet       │────│   Protected     │
│   Traffic       │    │   DNS Filter     │    │   Network       │
│                 │    │   (Go Service)   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ├── Threat Intelligence
                                ├── Ad Blocking Lists  
                                ├── DNS Resolution
                                └── Analytics
                                │
                                ▼
                       ┌──────────────────┐
                       │   API Gateway    │
                       │   (Node.js)      │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Dashboard      │
                       │   (React)        │
                       └──────────────────┘
```

## 🚀 Services

- **dns-filter/**: Go-based DNS filtering service with threat intelligence
- **threat-updater/**: Automated threat feed collection and processing
- **api-gateway/**: Node.js API server for management and analytics
- **dashboard/**: React-based control panel and monitoring

## 🛠️ Development

### Prerequisites
- Go 1.21+
- Node.js 18+
- Docker & Docker Compose
- kubectl (for K8s deployment)

### Quick Start
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f dns-filter

# Stop services
docker-compose down
```

### Testing
```bash
# Run comprehensive e2e tests
cd e2e
python scripts/run_all_tests.py --report-html reports/html/

# Test DNS functionality
nslookup google.com 127.0.0.1       # Should resolve
nslookup doubleclick.net 127.0.0.1   # Should be blocked

# Run network simulation
python scripts/run_all_tests.py --simulation-duration 30
```

## 📁 Project Structure

```
guardnet/
├── services/
│   ├── dns-filter/             # Go DNS filtering service
│   │   ├── cmd/               # Application entrypoints
│   │   │   └── threat-updater/ # Threat intelligence updater
│   │   ├── internal/          # Private application code
│   │   │   ├── config/        # Configuration management
│   │   │   ├── db/           # Database operations
│   │   │   └── feeds/        # Threat feed processing
│   │   └── pkg/              # Public library code
│   ├── api-gateway/           # Node.js API service
│   └── dashboard/             # React frontend
├── e2e/                       # End-to-end testing suite
│   ├── scripts/              # Test runners and utilities
│   ├── tests/                # Test categories
│   │   ├── dns_filtering/    # Core DNS functionality tests
│   │   ├── ad_blocking/      # Ad blocking tests
│   │   ├── threat_intel/     # Threat intelligence tests
│   │   ├── router_deployment/# Router integration tests
│   │   ├── network_simulation/# Multi-device scenarios
│   │   └── performance/      # Load and performance tests
│   └── utils/                # Testing utilities
├── infrastructure/
│   ├── docker/               # Docker configurations
│   └── kubernetes/           # K8s manifests
├── router-config/            # Router configuration templates
├── docs/                     # Documentation
└── scripts/                  # Build and deployment scripts
```

## 🔧 Configuration

Each service has its own configuration:
- DNS Filter: `services/dns-filter/configs/`
- API Gateway: `services/api-gateway/config/`
- Dashboard: `services/dashboard/.env`

## 📊 Performance Metrics

Recent test results from e2e testing suite:

### Family Network Simulation (60s):
- **158 DNS queries** processed across 6 devices
- **35.4% block rate** (56 ads/threats blocked)
- **96.8% success rate** with 13ms average response time
- **140 MB bandwidth saved** and 28 seconds faster loading

### Business Network Simulation (60s):
- **86 DNS queries** processed across 3 devices  
- **40.7% block rate** (35 ads/threats blocked)
- **100% success rate** with 12.6ms average response time
- **87.5 MB bandwidth saved** and 17.5 seconds faster loading

## 📊 Monitoring

- Health checks: `/health` endpoint on each service
- Threat intelligence: Real-time feed updates every 5 minutes
- DNS resolution: Sub-15ms response times with caching
- Logs: Structured JSON logging with threat detection details

## 🚢 Deployment

### Development
```bash
docker-compose up
```

### Production
```bash
kubectl apply -f infrastructure/kubernetes/
```

## 📝 API Documentation

API documentation available at: `docs/api/`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open pull request

## 📄 License

[License TBD]