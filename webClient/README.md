# WaddlePerf webClient

Browser-based network performance testing client with real-time visualization and WebSocket streaming.

## Overview

The WaddlePerf webClient is a full-stack web application consisting of:

- **Backend (Flask + SocketIO)**: API server that proxies test requests to testServer and manages authentication
- **Frontend (React + TypeScript)**: Interactive UI with real-time charts, gauges, and test configuration

## Features

### Backend (Flask API)
- WebSocket support for real-time test streaming
- Authentication with managerServer (optional)
- Session management via MariaDB Galera
- RESTful API endpoints for all test types (HTTP, TCP, UDP, ICMP)
- Health check endpoint
- Input validation and security best practices
- Production-ready with Gunicorn and eventlet workers

### Frontend (React)
- Modern React with TypeScript and hooks
- Real-time line charts showing latency over time (Recharts)
- Live gauges for throughput, jitter, and packet loss
- Interactive test configuration forms
- Protocol selection (HTTP/1.1/2/3, TCP, UDP, ICMP)
- WebSocket client for streaming results
- Login flow with authentication support
- Responsive design (mobile-friendly)
- Good console logging (no sensitive data)

## Architecture

```
┌─────────────────┐          ┌──────────────────┐          ┌─────────────┐
│   React Frontend│          │   Flask Backend  │          │ testServer  │
│   (Port 3000)   │◄────────►│   (Port 5000)    │◄────────►│ (Port 8080) │
│   - UI          │ HTTP/WS  │   - Proxy        │  HTTP    │ - Tests     │
│   - Charts      │          │   - Auth         │          │ - Results   │
└─────────────────┘          └──────────────────┘          └─────────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │ MariaDB Galera│
                              │ - Sessions    │
                              │ - Users       │
                              └───────────────┘
```

## Prerequisites

- **For Development**:
  - Python 3.13+
  - Node.js 20+
  - MariaDB/MySQL server

- **For Docker Deployment**:
  - Docker 20.10+
  - Docker Compose (optional)

## Quick Start (Development)

### 1. Backend Setup

```bash
cd webClient/api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run development server
python app.py
```

The API will be available at `http://localhost:5000`

### 2. Frontend Setup

```bash
cd webClient/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API URL

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Environment Configuration

### Backend (.env)

```bash
# Flask
SECRET_KEY=generate-random-secret-key-here
DEBUG=false
SESSION_COOKIE_SECURE=true

# CORS
FRONTEND_URL=http://localhost:3000,https://webclient.example.com

# External services
MANAGER_URL=http://localhost:5001
TESTSERVER_URL=http://localhost:8080

# Authentication
AUTH_ENABLED=true

# Database (MariaDB Galera)
DB_HOST=localhost
DB_PORT=3306
DB_USER=waddleperf
DB_PASS=waddleperf
DB_NAME=waddleperf
```

### Frontend (.env)

```bash
# API Backend URL
VITE_API_URL=http://localhost:5000
```

## Docker Deployment

### Build Images

```bash
# Build API image
docker build -f Dockerfile.api -t waddleperf-webclient-api:latest .

# Build Frontend image
docker build -f Dockerfile.frontend -t waddleperf-webclient-frontend:latest .
```

### Run with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  webclient-api:
    image: waddleperf-webclient-api:latest
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - FRONTEND_URL=${FRONTEND_URL}
      - MANAGER_URL=${MANAGER_URL}
      - TESTSERVER_URL=${TESTSERVER_URL}
      - AUTH_ENABLED=${AUTH_ENABLED}
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_USER=${DB_USER}
      - DB_PASS=${DB_PASS}
      - DB_NAME=${DB_NAME}
    depends_on:
      - mariadb
    restart: unless-stopped

  webclient-frontend:
    image: waddleperf-webclient-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:5000
    restart: unless-stopped

  mariadb:
    image: mariadb:11
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}
      - MYSQL_USER=${DB_USER}
      - MYSQL_PASSWORD=${DB_PASS}
    volumes:
      - mariadb_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mariadb_data:
```

Run:

```bash
docker-compose up -d
```

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check authentication status

### Test Execution
- `POST /api/test/http` - Run HTTP test
- `POST /api/test/tcp` - Run TCP test
- `POST /api/test/udp` - Run UDP test
- `POST /api/test/icmp` - Run ICMP test

### WebSocket Events

**Client → Server:**
- `start_test` - Start a new test with real-time updates

**Server → Client:**
- `connected` - Connection established
- `test_started` - Test execution started
- `test_progress` - Progress update (0-100%)
- `test_complete` - Test finished with results
- `error` - Error occurred

## Test Request Example

### HTTP POST Request

```bash
curl -X POST http://localhost:5000/api/test/http \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "port": 443,
    "timeout": 30,
    "count": 10,
    "protocol_detail": "HTTP/2"
  }'
```

### WebSocket Test (JavaScript)

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected');

  socket.emit('start_test', {
    test_type: 'http',
    target: 'example.com',
    port: 443,
    timeout: 30,
    count: 10
  });
});

socket.on('test_progress', (data) => {
  console.log('Progress:', data.progress + '%');
});

socket.on('test_complete', (data) => {
  console.log('Results:', data);
});
```

## Development

### Backend Development

```bash
cd webClient/api

# Install dev dependencies
pip install pytest pytest-cov flake8

# Run linting
flake8 .

# Run type check
python -m py_compile app.py wsgi.py

# Run tests (when available)
pytest
```

### Frontend Development

```bash
cd webClient/frontend

# Run development server with hot reload
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Production Deployment

### Security Considerations

1. **Use HTTPS**: Always use TLS/SSL in production
2. **Secure Cookies**: Set `SESSION_COOKIE_SECURE=true`
3. **Strong Secret**: Generate a strong `SECRET_KEY`
4. **Database Security**: Use strong passwords and limit network access
5. **CORS**: Restrict `FRONTEND_URL` to your domain only

### Performance Optimization

1. **Gunicorn Workers**: Adjust worker count based on CPU cores
2. **Database Connection Pool**: Configure appropriate pool size
3. **Nginx Reverse Proxy**: Use nginx for static file serving and load balancing
4. **CDN**: Serve static assets via CDN for better performance

### Monitoring

- Backend logs: Check gunicorn output
- Frontend logs: Browser console
- Health endpoint: `GET /health`
- Database metrics: Monitor MariaDB Galera cluster

## Multi-Architecture Support

Both Docker images support:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

Images are automatically built and published via GitHub Actions on push to main branch.

## CI/CD

GitHub Actions workflow (`.github/workflows/webclient.yml`):
- Runs tests for both API and frontend
- Builds multi-architecture Docker images
- Pushes to GitHub Container Registry (ghcr.io)

**Image Tags:**
- `latest` - Main branch builds
- `alpha` - Non-main branch builds
- `v*` - Release tags (semver)

## Troubleshooting

### Backend Issues

**Database Connection Failed**
```
Check DB_HOST, DB_PORT, DB_USER, DB_PASS in .env
Ensure MariaDB is running and accessible
```

**WebSocket Connection Failed**
```
Check CORS configuration in FRONTEND_URL
Ensure eventlet is installed (pip install eventlet)
```

**Authentication Errors**
```
Verify AUTH_ENABLED setting
Check user credentials in database
Ensure session table exists
```

### Frontend Issues

**API Connection Failed**
```
Check VITE_API_URL in .env
Ensure backend is running
Check browser console for CORS errors
```

**Build Errors**
```
Delete node_modules and package-lock.json
Run: npm install
Try: npm run build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

Part of the WaddlePerf project by Penguin Technologies Inc.

## Support

- GitHub Issues: https://github.com/penguintechinc/WaddlePerf/issues
- Documentation: See main README.md

## Version History

- **v1.0.0** (Current)
  - Initial release
  - Complete Flask backend with WebSocket support
  - React frontend with real-time charts
  - Multi-protocol testing (HTTP, TCP, UDP, ICMP)
  - Multi-architecture Docker builds
  - GitHub Actions CI/CD
