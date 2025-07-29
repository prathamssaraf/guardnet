# Docker Setup Guide for GuardNet

## 🐳 **Docker Installation for Windows**

### **Step 1: Download Docker Desktop**
1. Go to: https://www.docker.com/products/docker-desktop-windows/
2. Click "Download Docker Desktop for Windows"
3. Run the installer (`Docker Desktop Installer.exe`)

### **Step 2: Installation Requirements**
**System Requirements:**
- Windows 10/11 64-bit (Pro, Enterprise, Education)
- WSL 2 feature enabled
- Virtualization enabled in BIOS
- At least 4GB RAM

**Enable WSL 2 (if not already enabled):**
```powershell
# Run as Administrator in PowerShell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart computer, then set WSL 2 as default
wsl --set-default-version 2
```

### **Step 3: Install and Configure**
1. **Run Docker Desktop Installer**
2. **Accept License Agreement**
3. **Choose Configuration:**
   - ✅ Enable WSL 2 integration
   - ✅ Add Docker to PATH
4. **Restart Computer** when installation completes
5. **Start Docker Desktop** from Start Menu

### **Step 4: Verify Installation**
```bash
# Check Docker version
docker --version

# Check Docker Compose version  
docker-compose --version

# Test Docker with hello-world
docker run hello-world
```

---

## 🚀 **Quick Start After Installation**

### **Start GuardNet Services**
```bash
# Navigate to project directory
cd "D:\New folder (2)"

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs dns-filter
```

### **Test DNS Filtering**
```bash
# Test DNS resolution (after services are up)
nslookup google.com 127.0.0.1:8053

# Test health endpoints
curl http://localhost:8080/health
curl http://localhost:3000/health  # API Gateway
curl http://localhost:3001/health  # Dashboard
```

### **Access Services**
- **DNS Filter**: `localhost:8053` (UDP)
- **API Gateway**: `http://localhost:3000`
- **Dashboard**: `http://localhost:3001`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Nginx**: `http://localhost:80`

---

## 🛠️ **Development Commands**

### **Service Management**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart dns-filter

# View service logs
docker-compose logs -f dns-filter

# Execute commands in running container
docker-compose exec dns-filter /bin/sh
```

### **Database Operations**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U guardnet -d guardnet

# View database logs
docker-compose logs postgres

# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d postgres
```

### **Debugging and Development**
```bash
# Build services locally
docker-compose build

# Force rebuild (ignore cache)
docker-compose build --no-cache

# View resource usage
docker stats

# Clean up unused containers/images
docker system prune
```

---

## 🔧 **Troubleshooting**

### **Common Issues:**

**1. Docker Desktop Won't Start**
- Ensure WSL 2 is installed and updated
- Check if Hyper-V is enabled
- Restart Docker Desktop service

**2. "docker: command not found"**
- Restart terminal/command prompt
- Check if Docker Desktop is running
- Verify PATH includes Docker directory

**3. Port Conflicts**
- Check if ports 53, 80, 3000, 3001, 5432, 6379 are available
- Stop conflicting services
- Modify `docker-compose.yml` port mappings if needed

**4. WSL 2 Issues**
```powershell
# Update WSL kernel
wsl --update

# Set WSL 2 as default
wsl --set-default-version 2

# Restart WSL
wsl --shutdown
```

**5. Permission Issues**
- Run Docker Desktop as Administrator
- Check Docker Desktop settings for file sharing permissions

### **Logs and Diagnostics**
```bash
# Docker system information
docker system info

# Docker Desktop logs location:
# %APPDATA%\Docker\log.txt

# Container logs
docker-compose logs --tail=50 dns-filter
```

---

## 🎯 **Production Deployment**

### **Environment Variables**
Create `.env` file:
```bash
# Database
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgres://guardnet:your-secure-password@postgres:5432/guardnet

# Redis
REDIS_URL=redis://redis:6379

# JWT Secret
JWT_SECRET=your-jwt-secret-key

# Environment
NODE_ENV=production
GO_ENV=production
```

### **Security Configuration**
```bash
# Use Docker secrets for production
echo "your-db-password" | docker secret create db_password -
echo "your-jwt-secret" | docker secret create jwt_secret -
```

### **Scaling Services**
```bash
# Scale DNS filter service
docker-compose up -d --scale dns-filter=3

# Load balancer configuration
docker-compose up -d --scale api-gateway=2
```

---

## 📋 **Pre-Installation Checklist**

- [ ] Windows 10/11 64-bit
- [ ] At least 4GB RAM available
- [ ] Administrator access
- [ ] Internet connection for downloads
- [ ] WSL 2 compatible system
- [ ] Virtualization enabled in BIOS

---

## 🆘 **Getting Help**

**If installation fails:**
1. Check Docker Desktop documentation: https://docs.docker.com/desktop/windows/
2. Verify system requirements
3. Check Windows Event Viewer for errors
4. Try running Docker Desktop as Administrator

**For GuardNet-specific issues:**
1. Check service logs: `docker-compose logs`
2. Verify all containers are running: `docker-compose ps`
3. Test individual components
4. Check GitHub issues: https://github.com/prathamssaraf/guardnet/issues

---

**Once Docker is installed, run: `make dev` to start the full GuardNet system!**