# GuardNet Docker Setup Status

## 🚀 Current Progress

### ✅ Working Services
- **PostgreSQL Database**: `localhost:5432` - ✓ Running
- **Redis Cache**: `localhost:6379` - ✓ Running  
- **API Gateway**: `localhost:3000` - ✓ Healthy with endpoints
- **Dashboard**: `localhost:3001` - ✓ React app serving
- **Nginx Load Balancer**: `localhost:80` - ✓ Routing traffic

### ⚠️ Current Issues
1. **DNS Filter Service**: Container runtime issue preventing startup via docker-compose
   - Binary builds correctly and works when tested individually
   - Likely Docker Desktop on Windows compatibility issue
   - Service can connect to database/Redis when network is available

## 📋 Quick Commands

### Start All Services
```bash
# Start core services (database, cache, API, dashboard, nginx)
docker-compose up -d postgres redis api-gateway dashboard nginx

# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs api-gateway
```

### Test Endpoints
```bash
# API Gateway health
curl http://localhost:3000/health

# Dashboard health  
curl http://localhost:3001/health

# DNS status via API
curl http://localhost:3000/api/dns/status

# Security metrics
curl http://localhost:3000/api/security/metrics
```

### Service Management
```bash
# Stop all services
docker-compose down

# Rebuild specific service
docker-compose build api-gateway

# Restart service
docker-compose restart dashboard

# View resource usage
docker stats
```

## 🌐 Available URLs
- **Dashboard UI**: http://localhost:3001
- **API Gateway**: http://localhost:3000  
- **Load Balancer**: http://localhost:80
- **Database**: localhost:5432 (internal)
- **Cache**: localhost:6379 (internal)

## 🔧 Service Details

### API Gateway (Node.js/Express)
- **Port**: 3000
- **Health**: `/health`
- **Endpoints**: DNS status, security metrics
- **Features**: Rate limiting, CORS, security headers

### Dashboard (React + Nginx)
- **Port**: 3001  
- **Tech**: React 18, TypeScript, Nginx
- **Features**: Security dashboard UI, responsive design

### Database (PostgreSQL 15)
- **Port**: 5432
- **Credentials**: guardnet/dev-password
- **Database**: guardnet

### Cache (Redis 7)
- **Port**: 6379
- **Features**: DNS caching, session storage

## 🛠️ Development

### Local Development
```bash
# Start development environment
docker-compose up -d

# Follow logs in real-time
docker-compose logs -f api-gateway dashboard

# Execute commands in container
docker-compose exec api-gateway /bin/bash
```

### Building Services
```bash
# Build all services
docker-compose build

# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build dashboard
```

## 📊 Health Monitoring

### Health Check Commands
```bash
# Check all service health
curl -s localhost:3000/health && curl -s localhost:3001/health && echo " - All services healthy"

# Check container health
docker-compose ps

# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## 🔍 Troubleshooting

### Common Issues
1. **Port conflicts**: Check if ports 80, 3000, 3001, 5432, 6379 are available
2. **Docker not running**: Ensure Docker Desktop is started
3. **Build failures**: Try `docker-compose build --no-cache`
4. **Permission issues**: Run Docker Desktop as Administrator

### Log Investigation
```bash
# View all logs
docker-compose logs

# Service-specific logs  
docker-compose logs --tail=50 api-gateway
docker-compose logs -f dashboard

# System logs
docker system events
```

### Reset Environment
```bash
# Complete reset (WARNING: Deletes all data)
docker-compose down -v
docker system prune -f
docker-compose up -d
```

## 📈 Next Steps

### To Fix DNS Filter
1. Investigate Docker Desktop WSL2 compatibility
2. Test alternative container runtimes
3. Add fallback startup methods
4. Implement container health checks

### Enhancements
1. Add environment-specific configs
2. Implement proper logging
3. Add monitoring/metrics collection
4. Set up automated testing

---

**Last Updated**: $(date)
**Status**: Core services operational, DNS filter needs investigation
**Ready for**: Development and testing of API/Dashboard features