# GuardNet - Intelligent Router Security Service

Enterprise-level internet protection through intelligent cloud-based filtering via customer routers.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Customer      │────│   GuardNet       │────│   Clean         │
│   Router        │    │   DNS Filter     │    │   Internet      │
│                 │    │   (Go Service)   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                │ API calls
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

- **dns-filter/**: Go-based DNS filtering service (core protection engine)
- **api-gateway/**: Node.js API server (authentication, management, analytics)
- **dashboard/**: React-based customer and admin dashboards

## 🛠️ Development

### Prerequisites
- Go 1.21+
- Node.js 18+
- Docker & Docker Compose
- kubectl (for K8s deployment)

### Quick Start
```bash
# Install dependencies
make install

# Start development environment
make dev

# Run tests
make test

# Build for production
make build
```

## 📁 Project Structure

```
guardnet/
├── services/
│   ├── dns-filter/          # Go DNS filtering service
│   │   ├── cmd/            # Application entrypoints
│   │   ├── internal/       # Private application code
│   │   ├── pkg/            # Public library code
│   │   └── configs/        # Configuration files
│   ├── api-gateway/        # Node.js API service
│   │   ├── src/            # Source code
│   │   ├── tests/          # Test files
│   │   └── config/         # Configuration
│   └── dashboard/          # React frontend
│       ├── src/            # Source code
│       ├── public/         # Static assets
│       └── tests/          # Test files
├── infrastructure/
│   ├── docker/             # Docker configurations
│   └── kubernetes/         # K8s manifests
├── shared/
│   ├── schemas/            # API schemas
│   └── types/              # Shared type definitions
├── docs/                   # Documentation
├── scripts/                # Build and deployment scripts
└── GuardNet-ProjectPlan.md # Project roadmap
```

## 🔧 Configuration

Each service has its own configuration:
- DNS Filter: `services/dns-filter/configs/`
- API Gateway: `services/api-gateway/config/`
- Dashboard: `services/dashboard/.env`

## 📊 Monitoring

- Health checks: `/health` endpoint on each service
- Metrics: Prometheus compatible
- Logs: Structured JSON logging

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