# WaddlePerf Architecture

**Version**: 2.0
**Last Updated**: November 12, 2025

## Overview

WaddlePerf is a distributed network performance testing and monitoring platform designed to test user experience between endpoints. The system consists of a centralized management server, high-performance test servers, and multiple client implementations.

## Architecture Principles

1. **Stateless Components**: All servers and clients are stateless, enabling horizontal scaling
2. **Centralized State**: MariaDB Galera cluster is the single source of truth for all persistence
3. **Multi-Protocol Support**: HTTP/1.1/2/3, TCP (raw/TLS/SSH), UDP (raw/DNS), ICMP (ping/traceroute)
4. **Authentication-First**: JWT, API keys, and user/password authentication on all endpoints
5. **Real-Time Updates**: WebSocket support for live test result streaming
6. **Microservices Architecture**: Independent, containerized services with well-defined APIs

## System Components

### 1. Database Layer - MariaDB Galera

**Technology**: MariaDB 11.2 with Galera Cluster support
**Purpose**: Centralized state and persistence for the entire platform

**Database Schema**:
- `organization_units` - Hierarchical organization structure for user delegation
- `users` - User accounts with roles, MFA, API keys
- `sessions` - Active user sessions for web UIs
- `jwt_tokens` - Issued JWT tokens with expiration tracking
- `server_keys` - Shared secret keys for server-to-server communication
- `server_test_results` - Test results from testServer executions
- `client_test_results` - Test results from client submissions
- `client_configs` - Per-device configuration for automated clients

**Features**:
- Connection pooling (100 max connections per service)
- UTF-8mb4 character set with unicode collation
- Automatic cleanup via stored procedures
- Views for common queries (recent tests, device stats)
- Index optimization for performance

### 2. testServer (Go)

**Technology**: Go 1.21, Gorilla Mux
**Purpose**: High-performance, multi-protocol network test execution

**Responsibilities**:
- Execute HTTP/1.1/2/3 tests with detailed timing metrics
- TCP testing (raw, TLS 1.2/1.3, SSH)
- UDP testing (raw packets, DNS queries)
- ICMP testing (ping, traceroute)
- Authentication validation (JWT, API keys, server keys)
- Test result storage in database

**Performance**: 100+ concurrent tests, 13 MB binary, 50 MB Docker image

### 3. managerServer API (Flask)

**Technology**: Python 3.13, Flask 3.0, SQLAlchemy, Gunicorn + gevent
**Purpose**: Management backend for authentication, user management, and statistics

**Responsibilities**:
- User authentication (username/password, MFA/TOTP)
- JWT token issuance and revocation
- User CRUD operations with role-based access control
- Organization Unit management
- Statistics aggregation and querying

### 4. managerServer Frontend (React + TypeScript)

**Technology**: React 18, TypeScript, Vite, Recharts
**Purpose**: Management dashboard for administrators

**Features**:
- User management with role assignment
- Organization Unit management
- Statistics visualization
- MFA setup with QR codes
- Light/dark/auto theme support

### 5. webClient API (Flask + Flask-SocketIO)

**Technology**: Python 3.13, Flask 3.0, Flask-SocketIO
**Purpose**: Backend for browser-based network testing with real-time updates

**Features**: WebSocket server for live test streaming, authentication proxy

### 6. webClient Frontend (React + TypeScript)

**Technology**: React 18, TypeScript, Vite, Recharts, Socket.IO
**Purpose**: Browser-based network testing interface

**Features**: Real-time charts, live gauges, interactive test forms

### 7. containerClient (Python)

**Technology**: Python 3.13, AsyncIO
**Purpose**: Automated scheduled testing for continuous monitoring

**Features**: Cron-like scheduling, multi-protocol testing, device auto-detection

### 8. goClient (Go Thick Client)

**Technology**: Go 1.21, Cobra CLI
**Purpose**: Cross-platform desktop client for manual and scheduled testing

**Platforms**: macOS (ARM64/AMD64), Windows (AMD64/ARM64), Linux (AMD64/ARM64)

## Authentication & Security

### Authentication Methods

1. **JWT Tokens**: HS256, 24-hour expiration, stored in database
2. **API Keys**: 64-char hex, SHA256 hashed, stored in users table
3. **Username/Password**: bcrypt with cost factor 12, optional MFA/TOTP
4. **Server Keys**: 64-char hex for server-to-server gRPC

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| global_admin | Full access to all features |
| global_reporter | Read-only across all OUs |
| ou_admin | Admin within assigned OU |
| ou_reporter | Read-only within assigned OU |
| user | Execute tests, view own results |

## Deployment

### Development
```bash
docker-compose up -d
```

**Services**:
- MariaDB: localhost:3306
- testServer: localhost:8080
- managerServer API: localhost:5000
- managerServer Frontend: localhost:3000
- webClient API: localhost:5001
- webClient Frontend: localhost:3001
- Adminer: localhost:8081

### Production
```bash
docker-compose up -d
```

**Recommended**: MariaDB Galera 3-node cluster, nginx load balancer, Kubernetes for orchestration

## Technology Stack

| Component | Technology |
|-----------|------------|
| Database | MariaDB 11.2 |
| Backend | Flask 3.0, Go 1.21 |
| Frontend | React 18, TypeScript, Vite |
| Authentication | JWT, bcrypt, TOTP |
| Real-Time | Socket.IO, WebSockets |
| Containerization | Docker, Docker Compose |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

## License

Copyright © 2025 Penguin Technologies Inc.
