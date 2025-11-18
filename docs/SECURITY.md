# WaddlePerf Security Documentation

**Version**: 4.0.0
**Last Updated**: November 17, 2025

## Table of Contents

- [Security Overview](#security-overview)
- [Container Security](#container-security)
- [Network Capabilities](#network-capabilities)
- [Authentication & Authorization](#authentication--authorization)
- [Database Security](#database-security)
- [Network Security](#network-security)
- [Secrets Management](#secrets-management)
- [Security Best Practices](#security-best-practices)
- [Reporting Security Issues](#reporting-security-issues)

---

## Security Overview

WaddlePerf follows defense-in-depth security principles with multiple layers of protection:

1. **Container Isolation**: All services run in isolated Docker containers
2. **Non-Root Users**: Containers run as non-privileged users (UID 1000)
3. **Minimal Privileges**: Linux capabilities granted only when required
4. **Authentication-First**: All APIs require authentication (JWT, API keys, or server keys)
5. **Encrypted Communications**: Support for TLS/SSL on all external interfaces
6. **Input Validation**: All user inputs validated and sanitized
7. **Secure Defaults**: Development credentials clearly marked and easily changed

---

## Container Security

### Non-Root User Execution

All WaddlePerf containers run as a non-root user for security isolation:

```dockerfile
# Create non-root user (UID 1000)
RUN groupadd -g 1000 waddleperf && \
    useradd -m -u 1000 -g waddleperf waddleperf

# Switch to non-root user
USER waddleperf
```

**Benefits**:
- Limits impact of container breakout vulnerabilities
- Prevents privilege escalation attacks
- Follows principle of least privilege
- Complies with security best practices (CIS Docker Benchmark)

### Image Security

**Base Images**:
- **Python services**: Debian-based images (`python:3.12-slim`) for compatibility and security updates
- **Go services**: Multi-stage builds with Debian builder (`golang:1.23-bookworm`) and Alpine runtime (`alpine:3.19`)
- **Frontend services**: Minimal nginx on Alpine (`nginx:alpine`)

**Security Practices**:
- Regular security updates via automated rebuilds
- Minimal attack surface with slim/alpine images
- No unnecessary packages installed
- Regular vulnerability scanning with GitHub Actions

---

## Network Capabilities

### Why Network Capabilities Are Required

WaddlePerf performs network diagnostic tests including **traceroute** and **ICMP ping** tests. These operations require **raw socket access**, which is a privileged operation on Linux systems.

**Technical Background**:
- Traceroute uses raw ICMP packets or raw TCP SYN packets with manipulated TTL (Time To Live) values
- ICMP ping requires raw socket access to send/receive ICMP Echo Request/Reply packets
- Raw sockets are restricted to processes with `CAP_NET_RAW` capability to prevent network abuse

### Security Approach: Capabilities Instead of Root

**Problem**: Traceroute traditionally requires root access (SUID binary or running as root)

**WaddlePerf Solution**: Use Linux capabilities to grant minimal required privileges without full root access

### Implementation Details

#### 1. File Capabilities (Inside Container)

File capabilities grant specific privileges to individual executables:

```dockerfile
# Install network diagnostic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    traceroute \
    tcptraceroute \
    libcap2-bin

# Grant CAP_NET_RAW to traceroute binaries only
RUN setcap cap_net_raw+ep /usr/bin/traceroute.db && \
    setcap cap_net_raw+ep /usr/sbin/tcptraceroute
```

**What this does**:
- `cap_net_raw+ep`: Grants CAP_NET_RAW capability to the executable
  - `e` (effective): Capability is effective when process starts
  - `p` (permitted): Capability is in permitted set
- Only these specific binaries can create raw sockets
- The rest of the container still runs as non-root user `waddleperf` (UID 1000)

#### 2. Container Capabilities (docker-compose.yml)

Container-level capabilities allow the container to use file capabilities:

```yaml
testserver:
  cap_add:
    - NET_RAW      # Required for raw socket access
    - NET_ADMIN    # Required for advanced network operations
```

**Why both are needed**:
- `NET_RAW`: Allows processes to use raw sockets (required for ICMP, TCP SYN with custom TTL)
- `NET_ADMIN`: Allows network interface configuration (required for some traceroute operations)

### Affected Components

The following WaddlePerf components require network capabilities:

#### testServer (Go)
**Purpose**: Executes trace tests (HTTP trace, TCP trace, UDP trace, ICMP traceroute)
**Location**: `/testServer/Dockerfile`, `docker-compose.yml` (testserver service)
**Capabilities**: `NET_RAW`, `NET_ADMIN`

#### containerClient (Python)
**Purpose**: Automated scheduled testing including trace tests
**Location**: `/containerClient/Dockerfile`, `docker-compose.yml` (containerclient service)
**Capabilities**: `NET_RAW`, `NET_ADMIN`

#### goClient (Native Binary)
**Purpose**: Desktop client for manual testing
**Location**: Installed on user's system (not containerized)
**Capabilities**: May require `sudo` or SUID bit depending on installation method

### Security Considerations

**What this DOES allow**:
- Running traceroute and ping utilities
- Creating raw ICMP and TCP sockets for diagnostic purposes
- Reading raw network packets for test result analysis

**What this DOES NOT allow**:
- Full root access to the container or host
- Arbitrary system modifications
- Access to other containers or host filesystem
- Network packet injection outside test scope

**Principle of Least Privilege**:
- Capabilities are granted only to specific binaries (`traceroute`, `tcptraceroute`)
- Container still runs as non-root user (`waddleperf`)
- Capabilities are required only for specific test types (trace tests)
- Other test types (HTTP, TCP, UDP without trace) do not need these capabilities

### Alternative Approaches Considered

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Run container as root | Simple | Major security risk, violates best practices | ❌ Rejected |
| SUID binaries | Traditional approach | Still requires root, security concerns | ❌ Rejected |
| Capabilities-based | Minimal privileges, non-root user | Requires cap_add in docker-compose | ✅ **Selected** |
| Userspace tools (Paris traceroute) | No privileges needed | Limited protocol support, less accurate | ❌ Not sufficient |

### Kubernetes Deployment

For Kubernetes deployments, grant capabilities in the pod security context:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: waddleperf-testserver
spec:
  containers:
  - name: testserver
    image: waddleperf-testserver:latest
    securityContext:
      capabilities:
        add:
          - NET_RAW
          - NET_ADMIN
      runAsUser: 1000
      runAsNonRoot: true
      allowPrivilegeEscalation: false
```

**Important**: Use Pod Security Standards (PSS) to enforce non-root execution while allowing specific capabilities.

---

## Authentication & Authorization

### Authentication Methods

#### 1. JWT Tokens (Web UIs)

**Algorithm**: HS256 (HMAC with SHA-256)
**Expiration**: 24 hours (configurable via `JWT_EXPIRATION_HOURS`)
**Storage**: Database table `jwt_tokens` with expiration tracking

**Security Features**:
- Tokens stored in database for revocation support
- Automatic cleanup of expired tokens
- Refresh token support
- Secure secret key generation required

**Configuration**:
```bash
# Generate secure JWT secret
JWT_SECRET=$(openssl rand -hex 32)
```

#### 2. API Keys (Programmatic Access)

**Format**: 64-character hexadecimal string
**Storage**: SHA256 hashed in `users.api_key_hash` field
**Use Cases**: goClient, containerClient, external integrations

**Security Features**:
- Keys never stored in plaintext (SHA256 hash only)
- Rate limiting to prevent abuse
- Per-user key rotation support
- Revocation via user account management

**Best Practices**:
- Rotate API keys quarterly
- Use environment variables, never hardcode
- Store in secrets management systems (Vault, AWS Secrets Manager)

#### 3. Username/Password with MFA

**Password Hashing**: bcrypt with cost factor 12
**MFA**: TOTP (Time-based One-Time Password) compatible with Google Authenticator, Authy

**Security Features**:
- Bcrypt automatically salts passwords
- Cost factor 12 provides ~250ms computation time (resistant to brute force)
- TOTP secret stored encrypted in database
- Account lockout after failed attempts (configurable)

**Password Policy**:
- Minimum 8 characters (configurable)
- Complexity requirements (uppercase, lowercase, numbers, symbols)
- Password history to prevent reuse
- Expiration policy (optional)

#### 4. Server Keys (Server-to-Server)

**Format**: 64-character hexadecimal shared secret
**Storage**: SHA256 hashed in `server_keys` table
**Use Cases**: testServer ↔ managerServer gRPC communication

**Security Features**:
- Mutual authentication
- Prevents unauthorized servers from joining the cluster
- Regular rotation schedule

---

## Database Security

### Galera Cluster Security

See [DATABASE.md](DATABASE.md) for comprehensive Galera security considerations.

**Key Security Features**:
- Row-based replication only (binlog_format=ROW)
- InnoDB with ACID compliance
- Encrypted replication (optional, recommended for production)
- Connection pooling with prepared statements (prevents SQL injection)

### SQL Injection Prevention

**Protection Mechanisms**:
1. **Parameterized Queries**: All database queries use bound parameters
2. **ORM Layer**: SQLAlchemy provides automatic escaping
3. **Input Validation**: All inputs validated before database access
4. **Least Privilege**: Database users have minimal required permissions

**Example** (Flask/SQLAlchemy):
```python
# ✅ SAFE - Parameterized query
user = db.session.query(User).filter(User.username == username).first()

# ❌ UNSAFE - String concatenation (NEVER do this)
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

### Database User Permissions

```sql
-- Application user (waddleperf)
GRANT SELECT, INSERT, UPDATE, DELETE ON waddleperf.* TO 'waddleperf'@'%';

-- Admin user (for migrations only)
GRANT ALL PRIVILEGES ON waddleperf.* TO 'waddleperf_admin'@'localhost';

-- Read-only user (for reporting)
GRANT SELECT ON waddleperf.* TO 'waddleperf_readonly'@'%';
```

### Database Encryption

**At-Rest Encryption** (Optional):
```ini
[mysqld]
innodb_encrypt_tables = ON
innodb_encrypt_log = ON
innodb_encryption_threads = 4
```

**In-Transit Encryption** (Recommended for production):
```ini
[mysqld]
require_secure_transport = ON
ssl_ca = /etc/mysql/certs/ca.pem
ssl_cert = /etc/mysql/certs/server-cert.pem
ssl_key = /etc/mysql/certs/server-key.pem
```

---

## Network Security

### TLS/SSL Configuration

**Supported Protocols**: TLS 1.2, TLS 1.3
**Cipher Suites**: Modern, forward-secret ciphers only

**nginx Configuration**:
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

### CORS Configuration

**Development**:
```python
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
```

**Production**:
```python
CORS_ORIGINS = [
    "https://manager.yourdomain.com",
    "https://webclient.yourdomain.com"
]
```

### Firewall Rules

**Recommended UFW Configuration**:
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MariaDB (only from trusted IPs)
sudo ufw allow from 10.0.0.0/8 to any port 3306

# Enable firewall
sudo ufw enable
```

### Rate Limiting

**nginx Rate Limiting**:
```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
        }

        location /api/v1/login {
            limit_req zone=login burst=10;
        }
    }
}
```

---

## Secrets Management

### Environment Variables

**Development**:
```bash
# .env file (chmod 600)
DB_ROOT_PASSWORD=dev_root_password
DB_PASS=dev_password
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production
MANAGER_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

**Production**:
```bash
# Generate secure random secrets
DB_ROOT_PASSWORD=$(openssl rand -base64 32)
DB_PASS=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
MANAGER_KEY=$(openssl rand -hex 32)
```

### Secrets Management Systems

**Recommended for Production**:

#### HashiCorp Vault
```bash
# Store secrets
vault kv put secret/waddleperf/db password="$DB_PASS"

# Retrieve in container
DB_PASS=$(vault kv get -field=password secret/waddleperf/db)
```

#### AWS Secrets Manager
```bash
# Store secrets
aws secretsmanager create-secret \
  --name waddleperf/db-password \
  --secret-string "$DB_PASS"

# Retrieve in container
DB_PASS=$(aws secretsmanager get-secret-value \
  --secret-id waddleperf/db-password \
  --query SecretString \
  --output text)
```

### Secret Rotation

**Recommended Rotation Schedule**:
- Database passwords: Quarterly
- API keys: Quarterly or on compromise
- JWT secrets: Annually
- Server keys: Annually
- TLS certificates: Automatic via Let's Encrypt (90 days)

---

## Security Best Practices

### 1. Change Default Credentials

**IMPORTANT**: Change the default admin password (`admin123`) immediately after installation!

```bash
# Login to managerServer frontend
# Navigate to user profile
# Change password to strong passphrase
```

### 2. Enable MFA for Admins

All admin accounts should enable MFA/TOTP:
1. Login to managerServer
2. Navigate to user profile
3. Scan QR code with authenticator app
4. Enter verification code
5. Save recovery codes securely

### 3. Use Strong Secrets

**Generate Secure Secrets**:
```bash
# 256-bit hex secret (64 characters)
openssl rand -hex 32

# 256-bit base64 secret
openssl rand -base64 32

# 512-bit hex secret (128 characters)
openssl rand -hex 64
```

### 4. Regular Updates

**Update Schedule**:
- Security patches: Immediately
- Minor updates: Monthly
- Major updates: Quarterly (with testing)

**Update Process**:
```bash
# Backup database
docker exec waddleperf-mariadb mysqldump -u waddleperf -p waddleperf > backup.sql

# Pull latest images
docker-compose pull

# Restart with new images
docker-compose down && docker-compose up -d
```

### 5. Monitor Logs

**Enable Centralized Logging**:
```bash
# Configure log aggregation (ELK, Splunk, CloudWatch)
docker-compose logs -f | tee waddleperf.log
```

**Monitor for**:
- Failed login attempts
- API authentication failures
- Unusual test patterns
- Database connection errors
- Container restarts

### 6. Network Segmentation

**Recommended Network Architecture**:
```
Internet
   ↓
[nginx reverse proxy]
   ↓
[DMZ - Frontend containers]
   ↓
[Internal Network - API containers]
   ↓
[Database Network - MariaDB Galera]
```

### 7. Backup Strategy

**Backup Frequency**:
- Database: Daily (automated)
- Configuration: On change
- Container volumes: Weekly

**Backup Script**:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
docker exec waddleperf-mariadb mysqldump -u waddleperf -p"$DB_PASS" waddleperf \
  | gzip > "/backup/waddleperf-$DATE.sql.gz"

# Encrypt backup
openssl enc -aes-256-cbc -salt -in "/backup/waddleperf-$DATE.sql.gz" \
  -out "/backup/waddleperf-$DATE.sql.gz.enc" -k "$BACKUP_PASSWORD"
```

---

## Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

**Contact**: security@penguintech.com

**Expected Response Time**: 48 hours

**PGP Key**: Available at https://penguintech.com/pgp-key.asc

**Disclosure Policy**: Coordinated disclosure with 90-day window

**Bug Bounty**: Contact security team for scope and rewards

---

## Security Audits

**Last Security Audit**: November 2025
**Next Scheduled Audit**: February 2026

**External Tools Used**:
- **Docker Bench for Security**: Container security checks
- **OWASP ZAP**: Web application security testing
- **Trivy**: Container image vulnerability scanning
- **SQLMap**: SQL injection testing
- **Nmap**: Network security assessment

---

## Compliance

WaddlePerf follows security best practices from:
- OWASP Top 10 (Web Application Security)
- CIS Docker Benchmark (Container Security)
- NIST Cybersecurity Framework
- PCI DSS (if processing payment data)
- GDPR (if processing EU user data)

---

**Copyright © 2025 Penguin Technologies Inc.**
