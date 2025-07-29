# Docker Quick Commands for GuardNet

## 🚀 **Quick Start (After Docker Installation)**

### **Start All Services**
```bash
# Start all services in background
docker-compose up -d

# Start with logs visible  
docker-compose up

# Build and start (force rebuild)
docker-compose up --build
```

### **Check Service Status**
```bash
# View running containers
docker-compose ps

# View service logs
docker-compose logs dns-filter
docker-compose logs -f api-gateway  # Follow logs

# View all logs
docker-compose logs
```

### **Test DNS Filtering**
```bash
# Test DNS resolution (Windows)
nslookup google.com 127.0.0.1:8053

# Test with curl (health checks)
curl http://localhost:8080/health     # DNS Filter
curl http://localhost:3000/health     # API Gateway  
curl http://localhost:3001/health     # Dashboard
curl http://localhost:8080/metrics    # Prometheus metrics
```

## 🛠️ **Development Commands**

### **Service Management**
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: Deletes data)
docker-compose down -v

# Restart specific service
docker-compose restart dns-filter

# Scale services
docker-compose up -d --scale dns-filter=2
```

### **Database Operations**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U guardnet -d guardnet

# Run SQL commands
docker-compose exec postgres psql -U guardnet -d guardnet -c "SELECT * FROM threat_domains LIMIT 5;"

# View database logs
docker-compose logs postgres
```

### **Cache Operations**
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View Redis info
docker-compose exec redis redis-cli info

# Monitor Redis commands
docker-compose exec redis redis-cli monitor
```

## 🔧 **Debugging & Troubleshooting**

### **Container Inspection**
```bash
# Execute shell in running container
docker-compose exec dns-filter /bin/sh
docker-compose exec api-gateway /bin/bash

# View container details
docker inspect guardnet_dns-filter_1

# View resource usage
docker stats
```

### **Logs and Debugging**
```bash
# View specific service logs
docker-compose logs --tail=50 dns-filter

# Follow logs from specific time
docker-compose logs --since="2024-01-01T12:00:00" dns-filter

# View all container logs
docker-compose logs --tail=100
```

### **Network and Port Issues**
```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect guardnet_guardnet

# Check port bindings
docker-compose port dns-filter 53
docker-compose port api-gateway 3000
```

## 🏗️ **Build and Development**

### **Rebuild Services**
```bash
# Rebuild specific service
docker-compose build dns-filter

# Rebuild without cache
docker-compose build --no-cache

# Pull latest base images
docker-compose pull
```

### **Development with Live Reload**
```bash
# Mount source code for development
# (Add volumes to docker-compose.yml for live reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 🧹 **Cleanup Commands**

### **Clean Docker System**
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused (BE CAREFUL!)
docker system prune -a
```

### **GuardNet Specific Cleanup**
```bash
# Stop and remove GuardNet containers
docker-compose down

# Remove GuardNet images
docker rmi guardnet_dns-filter guardnet_api-gateway guardnet_dashboard

# Remove GuardNet volumes
docker volume rm guardnet_postgres_data guardnet_redis_data
```

## 📊 **Monitoring and Metrics**

### **Service Health Checks**
```bash
# Check all health endpoints
curl -s http://localhost:8080/health | jq
curl -s http://localhost:3000/health | jq  
curl -s http://localhost:3001/health | jq

# Check metrics
curl -s http://localhost:8080/metrics | grep guardnet
```

### **Performance Monitoring**
```bash
# View resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# View system information
docker system df
docker system info
```

## 🚀 **Production Deployment**

### **Environment Setup**
```bash
# Create production environment file
cp .env.example .env.production

# Start with production environment
docker-compose --env-file .env.production up -d
```

### **Backup and Restore**
```bash
# Backup database
docker-compose exec postgres pg_dump -U guardnet guardnet > backup.sql

# Restore database
docker-compose exec -T postgres psql -U guardnet -d guardnet < backup.sql

# Backup volumes
docker run --rm -v guardnet_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## ⚡ **One-Line Commands**

```bash
# Complete restart
docker-compose down && docker-compose up -d

# View all logs in real-time
docker-compose logs -f --tail=10

# Quick health check all services
curl -s localhost:8080/health && curl -s localhost:3000/health && echo "All services healthy"

# DNS test with dig (if available)
dig @127.0.0.1 -p 8053 google.com

# Complete reset (WARNING: Deletes all data)
docker-compose down -v && docker-compose up -d
```

## 🆘 **Common Issues & Solutions**

### **Port Already in Use**
```bash
# Find what's using the port
netstat -ano | findstr :53
netstat -ano | findstr :3000

# Kill process using port (Windows)
taskkill /PID <PID> /F
```

### **Services Won't Start**
```bash
# Check Docker daemon is running
docker version

# Restart Docker service
# On Windows: Restart Docker Desktop

# Check for syntax errors
docker-compose config
```

### **Database Connection Issues**
```bash
# Verify PostgreSQL is accessible
docker-compose exec postgres pg_isready -U guardnet

# Check connection from DNS service
docker-compose exec dns-filter ping postgres
```

---

**💡 Pro Tip**: Create aliases for common commands:
```bash
alias dcup="docker-compose up -d"
alias dcdown="docker-compose down"  
alias dclogs="docker-compose logs -f"
alias dcps="docker-compose ps"
```