# Deploy GuardNet - Step by Step

## 🐳 **Quick Docker Installation (5 minutes)**

### **Step 1: Install Docker Desktop**
1. Download: https://www.docker.com/products/docker-desktop-windows/
2. Run installer and restart computer
3. Start Docker Desktop from Start Menu

### **Step 2: Deploy GuardNet**
```bash
# Navigate to project
cd "D:\New folder (2)"

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### **Step 3: Access Services**
Once deployed, these links will be available:

## 🌐 **Service Links (After Deployment)**

### **Main Services**
- **DNS Filter Health**: http://localhost:8080/health
- **DNS Filter Metrics**: http://localhost:8080/metrics
- **API Gateway**: http://localhost:3000/health  
- **Dashboard**: http://localhost:3001
- **Main Proxy**: http://localhost:80

### **Database & Cache**
- **PostgreSQL**: localhost:5432 (use database client)
- **Redis**: localhost:6379 (use Redis client)

### **Monitoring**
- **Prometheus Metrics**: http://localhost:8080/metrics
- **System Health**: http://localhost:8080/ready

## 🧪 **Test DNS Filtering**
```bash
# Test DNS resolution
nslookup google.com 127.0.0.1:8053

# Test threat blocking
nslookup malware-test.com 127.0.0.1:8053
```

## 📊 **Expected Responses**

### **Health Check Response:**
```json
{
  "status": "healthy",
  "service": "dns-filter", 
  "timestamp": "2025-01-29T21:30:00Z"
}
```

### **Metrics Sample:**
```
guardnet_dns_queries_total 1234
guardnet_dns_blocked_total 56
guardnet_dns_allowed_total 1178
```

## 🛑 **If Docker Installation Fails**

Use the alternative deployment below.