# WaddlePerf Installation Guide

**Version**: 2.0
**Last Updated**: November 12, 2025

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker Compose)](#quick-start-docker-compose)
- [Production Deployment](#production-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Bare Metal Installation](#bare-metal-installation)
- [Client Installation](#client-installation)
- [Post-Installation](#post-installation)
- [Upgrading](#upgrading)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum** (Development/Testing):
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB
- Network: 100 Mbps

**Recommended** (Production):
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD
- Network: 1 Gbps+

**Supported Operating Systems**:
- Linux (Ubuntu 22.04+, Debian 11+, RHEL 8+, CentOS 8+)
- macOS 12+ (for goClient only)
- Windows 10/11 (for goClient only)

---

### Software Dependencies

#### For Docker Deployment (Recommended)

**Required**:
- Docker Engine 20.10+ or Docker Desktop 4.0+
- Docker Compose 2.0+

**Installation**:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# macOS
Download Docker Desktop from https://www.docker.com/products/docker-desktop

# Windows
Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### For Kubernetes Deployment

**Required**:
- Kubernetes 1.24+
- kubectl CLI tool
- Helm 3.0+ (optional but recommended)

#### For Development/Building

**Required**:
- Git
- Node.js 18+ and npm 9+ (for frontend development)
- Go 1.21+ (for Go components)
- Python 3.13+ (for Python components)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y git nodejs npm golang-go python3 python3-pip python3-venv

# macOS (with Homebrew)
brew install git node go python@3.13

# Verify installations
docker --version
docker-compose --version
git --version
node --version
npm --version
go version
python3 --version
```

---

## Quick Start (Docker Compose)

This is the fastest way to get WaddlePerf running for development or testing.

### 1. Clone the Repository

```bash
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings (optional for development):

```bash
# Minimal configuration for development
DB_ROOT_PASSWORD=your_secure_root_password
DB_PASS=your_secure_db_password
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
MANAGER_KEY=$(openssl rand -hex 32)
```

**Important**: For production, change all default passwords and generate secure secrets!

### 3. Start All Services

```bash
# Development mode (with live reload)
docker-compose -f docker-compose.dev.yml up -d

# Or production mode
docker-compose up -d
```

### 4. Verify Installation

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f

# Check health endpoints
curl http://localhost:8080/health  # testServer
curl http://localhost:5000/health  # managerServer API
curl http://localhost:5001/health  # webClient API
```

### 5. Access the Interfaces

- **managerServer Frontend**: http://localhost:3000
- **webClient Frontend**: http://localhost:3001
- **Adminer (Database UI)**: http://localhost:8081

**Default Credentials**:
- Username: `admin`
- Password: `admin123`

**IMPORTANT**: Change this password immediately after first login!

---

## Production Deployment

For production environments, follow these steps for a secure and scalable deployment.

### 1. Server Preparation

#### Firewall Configuration

```bash
# Ubuntu/Debian with UFW
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 3306/tcp    # MariaDB (if external access needed)
sudo ufw enable

# CentOS/RHEL with firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload
```

#### System Limits

Add to `/etc/security/limits.conf`:

```
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
```

### 2. Environment Configuration

Create production `.env` file:

```bash
# ========================================
# Database Configuration
# ========================================
DB_ROOT_PASSWORD=$(openssl rand -base64 32)
DB_NAME=waddleperf
DB_USER=waddleperf
DB_PASS=$(openssl rand -base64 32)
DB_HOST=mariadb  # or external DB hostname
DB_PORT=3306

# ========================================
# Security Keys (NEVER commit these!)
# ========================================
MANAGER_KEY=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# ========================================
# JWT Configuration
# ========================================
JWT_EXPIRATION_HOURS=24

# ========================================
# Authentication
# ========================================
AUTH_ENABLED=true
MFA_REQUIRED=false  # Set to true to require MFA for all users

# ========================================
# testServer Configuration
# ========================================
MAX_CONCURRENT_TESTS=200
LOG_LEVEL=info

# ========================================
# CORS Configuration
# ========================================
CORS_ORIGINS=https://manager.yourdomain.com,https://webclient.yourdomain.com

# ========================================
# External URLs (for production)
# ========================================
MANAGER_API_URL=https://manager-api.yourdomain.com
WEBCLIENT_API_URL=https://webclient-api.yourdomain.com
TESTSERVER_URL=https://testserver.yourdomain.com
```

**Security Best Practices**:
- Store `.env` file with `chmod 600` permissions
- Never commit `.env` to version control
- Use environment-specific `.env` files
- Rotate secrets regularly

### 3. Database Setup

#### Option A: Docker MariaDB (Single Node)

```bash
docker-compose up -d mariadb
```

#### Option B: External MariaDB Galera Cluster

For high availability, use a 3-node Galera cluster:

```bash
# On each node, install MariaDB
sudo apt-get install mariadb-server galera-4

# Configure /etc/mysql/mariadb.conf.d/60-galera.cnf
[galera]
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so
wsrep_cluster_address="gcomm://node1-ip,node2-ip,node3-ip"
wsrep_cluster_name="waddleperf_cluster"
wsrep_node_address="this-node-ip"
wsrep_node_name="node1"
binlog_format=row
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2

# Bootstrap first node
sudo galera_new_cluster

# Start other nodes
sudo systemctl start mariadb

# Import schema
mysql -u root -p < database/schema.sql
```

### 4. SSL/TLS Certificates

#### Option A: Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d manager.yourdomain.com
sudo certbot certonly --standalone -d webclient.yourdomain.com
sudo certbot certonly --standalone -d testserver.yourdomain.com

# Certificates will be in /etc/letsencrypt/live/
```

#### Option B: Self-Signed (Development Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/waddleperf.key \
  -out /etc/ssl/certs/waddleperf.crt
```

### 5. Reverse Proxy (nginx)

Install and configure nginx as reverse proxy:

```bash
sudo apt-get install nginx
```

Create `/etc/nginx/sites-available/waddleperf`:

```nginx
# managerServer Frontend
server {
    listen 443 ssl http2;
    server_name manager.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/manager.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/manager.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# managerServer API
server {
    listen 443 ssl http2;
    server_name manager-api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/manager-api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/manager-api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# webClient Frontend
server {
    listen 443 ssl http2;
    server_name webclient.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/webclient.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webclient.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# webClient API (with WebSocket support)
server {
    listen 443 ssl http2;
    server_name webclient-api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/webclient-api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webclient-api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# testServer
server {
    listen 443 ssl http2;
    server_name testserver.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/testserver.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/testserver.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name manager.yourdomain.com webclient.yourdomain.com testserver.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

Enable and start nginx:

```bash
sudo ln -s /etc/nginx/sites-available/waddleperf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Start Production Services

```bash
docker-compose up -d
```

### 7. Enable Automatic Startup

```bash
# Create systemd service for docker-compose
sudo tee /etc/systemd/system/waddleperf.service <<EOF
[Unit]
Description=WaddlePerf Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/waddleperf
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable waddleperf
```

---

## Kubernetes Deployment

For large-scale deployments, use Kubernetes for orchestration.

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Persistent storage provider
- Ingress controller (nginx-ingress recommended)

### 1. Create Namespace

```bash
kubectl create namespace waddleperf
```

### 2. Create Secrets

```bash
# Database credentials
kubectl create secret generic db-credentials \
  --from-literal=root-password=$(openssl rand -base64 32) \
  --from-literal=user=waddleperf \
  --from-literal=password=$(openssl rand -base64 32) \
  -n waddleperf

# Application secrets
kubectl create secret generic app-secrets \
  --from-literal=manager-key=$(openssl rand -hex 32) \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  -n waddleperf
```

### 3. Deploy MariaDB Galera Cluster

Create `mariadb-galera.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mariadb-galera
  namespace: waddleperf
spec:
  ports:
  - port: 3306
    name: mysql
  clusterIP: None
  selector:
    app: mariadb-galera
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mariadb-galera
  namespace: waddleperf
spec:
  serviceName: mariadb-galera
  replicas: 3
  selector:
    matchLabels:
      app: mariadb-galera
  template:
    metadata:
      labels:
        app: mariadb-galera
    spec:
      containers:
      - name: mariadb
        image: mariadb:11.2
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: root-password
        - name: MYSQL_DATABASE
          value: waddleperf
        - name: MYSQL_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: user
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
```

Apply:

```bash
kubectl apply -f mariadb-galera.yaml
```

### 4. Deploy WaddlePerf Services

Create `waddleperf-deployment.yaml`:

```yaml
---
# testServer Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: testserver
  namespace: waddleperf
spec:
  replicas: 3
  selector:
    matchLabels:
      app: testserver
  template:
    metadata:
      labels:
        app: testserver
    spec:
      containers:
      - name: testserver
        image: ghcr.io/penguincloud/waddleperf-testserver:latest
        env:
        - name: DB_HOST
          value: mariadb-galera
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: user
        - name: DB_PASS
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: MANAGER_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: manager-key
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
---
# testServer Service
apiVersion: v1
kind: Service
metadata:
  name: testserver
  namespace: waddleperf
spec:
  selector:
    app: testserver
  ports:
  - port: 8080
    targetPort: 8080
---
# managerServer API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: manager-api
  namespace: waddleperf
spec:
  replicas: 2
  selector:
    matchLabels:
      app: manager-api
  template:
    metadata:
      labels:
        app: manager-api
    spec:
      containers:
      - name: manager-api
        image: ghcr.io/penguincloud/waddleperf-manager-api:latest
        env:
        - name: DB_HOST
          value: mariadb-galera
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: user
        - name: DB_PASS
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt-secret
        ports:
        - containerPort: 5000
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
# managerServer API Service
apiVersion: v1
kind: Service
metadata:
  name: manager-api
  namespace: waddleperf
spec:
  selector:
    app: manager-api
  ports:
  - port: 5000
    targetPort: 5000
---
# Add similar deployments for:
# - managerServer Frontend
# - webClient API
# - webClient Frontend
# - containerClient (as DaemonSet for node monitoring)
```

Apply:

```bash
kubectl apply -f waddleperf-deployment.yaml
```

### 5. Create Ingress

Create `waddleperf-ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: waddleperf-ingress
  namespace: waddleperf
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - manager.yourdomain.com
    - webclient.yourdomain.com
    - testserver.yourdomain.com
    secretName: waddleperf-tls
  rules:
  - host: manager.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: manager-frontend
            port:
              number: 80
  - host: testserver.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: testserver
            port:
              number: 8080
```

Apply:

```bash
kubectl apply -f waddleperf-ingress.yaml
```

---

## Bare Metal Installation

For bare metal installations without Docker.

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  mariadb-server \
  nginx \
  python3 python3-pip python3-venv \
  golang-go \
  nodejs npm \
  git wget curl

# Start MariaDB
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

### 2. Configure Database

```bash
# Secure MariaDB
sudo mysql_secure_installation

# Create database and user
sudo mysql <<EOF
CREATE DATABASE waddleperf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'waddleperf'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON waddleperf.* TO 'waddleperf'@'localhost';
FLUSH PRIVILEGES;
EOF

# Import schema
mysql -u waddleperf -p waddleperf < database/schema.sql
```

### 3. Build and Install testServer

```bash
cd testServer
go mod download
go build -o /usr/local/bin/waddleperf-testserver ./cmd/testserver

# Create systemd service
sudo tee /etc/systemd/system/waddleperf-testserver.service <<EOF
[Unit]
Description=WaddlePerf testServer
After=network.target mariadb.service

[Service]
Type=simple
User=waddleperf
Environment="DB_HOST=localhost"
Environment="DB_USER=waddleperf"
Environment="DB_PASS=your_secure_password"
Environment="PORT=8080"
ExecStart=/usr/local/bin/waddleperf-testserver
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable waddleperf-testserver
sudo systemctl start waddleperf-testserver
```

### 4. Install managerServer API

```bash
cd managerServer/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/waddleperf-manager.service <<EOF
[Unit]
Description=WaddlePerf managerServer API
After=network.target mariadb.service

[Service]
Type=simple
User=waddleperf
WorkingDirectory=/opt/waddleperf/managerServer/api
Environment="DB_HOST=localhost"
Environment="DB_USER=waddleperf"
Environment="DB_PASS=your_secure_password"
Environment="SECRET_KEY=your_secret_key"
Environment="JWT_SECRET=your_jwt_secret"
ExecStart=/opt/waddleperf/managerServer/api/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable waddleperf-manager
sudo systemctl start waddleperf-manager
```

### 5. Build and Serve Frontends

```bash
# managerServer Frontend
cd managerServer/frontend
npm install
npm run build
sudo cp -r dist /var/www/html/manager

# webClient Frontend
cd webClient/frontend
npm install
npm run build
sudo cp -r dist /var/www/html/webclient

# Configure nginx (see Production Deployment section)
```

---

## Client Installation

### goClient (Desktop)

See [USAGE.md goClient section](USAGE.md#goclient-usage) for detailed installation instructions.

### containerClient (Docker)

See [USAGE.md containerClient section](USAGE.md#containerclient-usage) for deployment options.

---

## Post-Installation

### 1. Initial Configuration

```bash
# Create admin user (if not exists)
docker exec -it waddleperf-manager-api python manage.py create-admin

# Or manually via database
docker exec -it waddleperf-mariadb mysql -u waddleperf -p waddleperf
```

SQL:

```sql
INSERT INTO users (username, email, password_hash, api_key, role, is_active)
VALUES (
  'admin',
  'admin@example.com',
  -- bcrypt hash of 'admin123'
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL6D0H0mPy',
  CONCAT(LOWER(HEX(RANDOM_BYTES(32)))),
  'global_admin',
  TRUE
);
```

### 2. Health Checks

```bash
# Check all services
curl http://localhost:8080/health
curl http://localhost:5000/health
curl http://localhost:5001/health

# Check database
docker exec waddleperf-mariadb mysql -u waddleperf -p -e "SHOW DATABASES;"
```

### 3. First Login

1. Navigate to http://localhost:3000 (or your domain)
2. Login with admin credentials
3. **Change default password immediately**
4. Create additional users as needed
5. Get API key from user profile

### 4. Run First Test

Using webClient:
1. Navigate to http://localhost:3001
2. Login with user credentials
3. Run an HTTP test to https://www.google.com

Using goClient:
```bash
waddleperf init-config
# Edit ~/.waddleperf/config.yaml with your API key
waddleperf run
```

### 5. Monitoring and Logs

```bash
# Docker Compose
docker-compose logs -f

# Kubernetes
kubectl logs -f deployment/testserver -n waddleperf

# Bare Metal
sudo journalctl -u waddleperf-testserver -f
sudo journalctl -u waddleperf-manager -f
```

---

## Upgrading

### Docker Compose Upgrade

```bash
# Pull latest images
docker-compose pull

# Backup database
docker exec waddleperf-mariadb mysqldump -u waddleperf -p waddleperf > backup.sql

# Stop services
docker-compose down

# Start with new images
docker-compose up -d

# Run migrations (if any)
docker exec waddleperf-manager-api python manage.py db upgrade
```

### Kubernetes Upgrade

```bash
# Update image tags in deployment YAML
kubectl apply -f waddleperf-deployment.yaml

# Or use rolling update
kubectl set image deployment/testserver testserver=ghcr.io/penguincloud/waddleperf-testserver:v2.0 -n waddleperf
```

### Bare Metal Upgrade

```bash
# Stop services
sudo systemctl stop waddleperf-testserver waddleperf-manager

# Backup
sudo cp -r /opt/waddleperf /opt/waddleperf.backup
mysqldump -u waddleperf -p waddleperf > backup.sql

# Pull updates
cd /opt/waddleperf
git pull

# Rebuild
cd testServer && go build -o /usr/local/bin/waddleperf-testserver ./cmd/testserver
cd managerServer/api && source venv/bin/activate && pip install -r requirements.txt --upgrade

# Start services
sudo systemctl start waddleperf-testserver waddleperf-manager
```

---

## Troubleshooting

### Database Connection Errors

**Problem**: Services cannot connect to MariaDB

**Solutions**:
```bash
# Check MariaDB is running
docker ps | grep mariadb

# Check credentials
grep DB_ .env

# Test connection
docker exec -it waddleperf-mariadb mysql -u waddleperf -p

# Check logs
docker logs waddleperf-mariadb
```

### Port Conflicts

**Problem**: Port already in use

**Solutions**:
```bash
# Find what's using the port
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# Kill the process or change port in docker-compose.yml
```

### Container Fails to Start

**Problem**: Container exits immediately

**Solutions**:
```bash
# Check logs
docker logs <container-name>

# Check resource limits
docker stats

# Verify environment variables
docker exec <container-name> env
```

### Frontend Not Loading

**Problem**: Blank page or 502 error

**Solutions**:
```bash
# Check API is running
curl http://localhost:5000/health

# Check CORS configuration
grep CORS .env

# Clear browser cache
# Check browser console for errors
```

### High Memory Usage

**Problem**: Services using too much memory

**Solutions**:
```bash
# Check current usage
docker stats

# Reduce resource limits in docker-compose.yml
# Reduce MAX_CONCURRENT_TESTS
# Add memory limits to containers
```

### SSL Certificate Errors

**Problem**: SSL/TLS certificate issues

**Solutions**:
```bash
# Renew Let's Encrypt certificates
sudo certbot renew

# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/domain/cert.pem -noout -dates

# Reload nginx
sudo systemctl reload nginx
```

---

## Getting Help

- **Documentation**: https://github.com/penguintechinc/WaddlePerf/tree/main/docs
- **Issues**: https://github.com/penguintechinc/WaddlePerf/issues
- **Discussions**: https://github.com/penguintechinc/WaddlePerf/discussions
- **Security Issues**: security@penguintech.com

---

**Copyright © 2025 Penguin Technologies Inc.**
