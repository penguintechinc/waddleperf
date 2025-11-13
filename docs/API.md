# WaddlePerf API Documentation

**Version**: 2.0
**Last Updated**: November 12, 2025

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [testServer API](#testserver-api)
- [managerServer API](#managerserver-api)
- [webClient API](#webclient-api)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)

## Overview

WaddlePerf provides three primary REST APIs:

1. **testServer API** - Execute network performance tests
2. **managerServer API** - User management and statistics
3. **webClient API** - Browser-based testing proxy with WebSocket support

All APIs return JSON responses and use standard HTTP status codes.

**Base URLs** (Development):
- testServer: `http://localhost:8080`
- managerServer API: `http://localhost:5000`
- webClient API: `http://localhost:5001`

## Authentication

### Authentication Methods

WaddlePerf supports multiple authentication methods:

#### 1. JWT Token
```http
Authorization: Bearer <jwt_token>
```

Obtain JWT from managerServer `/api/v1/auth/login` endpoint. Tokens expire after 24 hours (configurable).

#### 2. API Key
```http
Authorization: Bearer <api_key>
```

API keys are 64-character hex strings generated per user. Obtain from user profile in managerServer UI.

#### 3. Username/Password (Basic Auth)
```http
Authorization: Basic <base64(username:password)>
```

Basic authentication is supported for initial login and legacy clients.

#### 4. Server Key (Server-to-Server)
```http
X-Manager-Key: <server_key>
```

64-character shared secret for internal service communication.

### Device Headers

All test endpoints accept optional device identification headers:

```http
X-Device-Serial: device-123
X-Device-Hostname: laptop-001
X-Device-OS: Linux
X-Device-OS-Version: 6.8.0-86-generic
```

---

## testServer API

High-performance test execution server written in Go.

### Health Check

**Endpoint**: `GET /health`
**Authentication**: None
**Description**: Check server health and version

#### Request Example
```bash
curl http://localhost:8080/health
```

#### Response Example
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### HTTP Test

**Endpoint**: `POST /api/v1/test/http`
**Authentication**: Required (JWT or API Key)
**Description**: Execute HTTP/HTTPS test with detailed timing metrics

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target | string | Yes | URL to test (e.g., https://example.com) |
| protocol | string | No | Protocol version: http1, http2, http3, auto (default: auto) |
| method | string | No | HTTP method: GET, POST, HEAD (default: GET) |
| timeout | integer | No | Timeout in seconds (default: 30) |
| follow_redirects | boolean | No | Follow HTTP redirects (default: true) |
| verify_tls | boolean | No | Verify TLS certificates (default: true) |

#### Request Example
```bash
curl -X POST http://localhost:8080/api/v1/test/http \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -H "X-Device-Serial: laptop-001" \
  -d '{
    "target": "https://www.google.com",
    "protocol": "auto",
    "method": "GET",
    "timeout": 30,
    "follow_redirects": true,
    "verify_tls": true
  }'
```

#### Response Example
```json
{
  "target": "https://www.google.com",
  "status_code": 200,
  "connected_proto": "HTTP/2.0",
  "latency_ms": 45.23,
  "ttfb_ms": 42.15,
  "dns_lookup_ms": 8.45,
  "tcp_connect_ms": 12.34,
  "tls_handshake_ms": 18.67,
  "total_time_ms": 125.78,
  "content_length_kb": 45.6,
  "transfer_speed_mbs": 3.2,
  "remote_addr": "142.250.185.68:443",
  "success": true,
  "error": null
}
```

---

### TCP Test

**Endpoint**: `POST /api/v1/test/tcp`
**Authentication**: Required (JWT or API Key)
**Description**: Execute TCP connection test (raw, TLS, or SSH)

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target | string | Yes | Host:port to test (e.g., example.com:443) |
| protocol | string | No | Protocol: raw, tls, ssh (default: raw) |
| timeout | integer | No | Timeout in seconds (default: 10) |
| verify_tls | boolean | No | Verify TLS certificates (default: true) |

#### Request Example
```bash
curl -X POST http://localhost:8080/api/v1/test/tcp \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "www.google.com:443",
    "protocol": "tls",
    "timeout": 10,
    "verify_tls": true
  }'
```

#### Response Example
```json
{
  "target": "www.google.com:443",
  "connected": true,
  "latency_ms": 12.45,
  "handshake_ms": 18.23,
  "remote_addr": "142.250.185.68:443",
  "local_addr": "192.168.1.100:54321",
  "tls_version": "TLS 1.3",
  "tls_cipher": "TLS_AES_128_GCM_SHA256",
  "success": true,
  "error": null
}
```

---

### UDP Test

**Endpoint**: `POST /api/v1/test/udp`
**Authentication**: Required (JWT or API Key)
**Description**: Execute UDP test (raw packets or DNS query)

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target | string | Yes | Host:port to test (e.g., 8.8.8.8:53) |
| protocol | string | No | Protocol: raw, dns (default: raw) |
| query | string | No | DNS query hostname (required if protocol=dns) |
| timeout | integer | No | Timeout in seconds (default: 5) |

#### Request Example
```bash
curl -X POST http://localhost:8080/api/v1/test/udp \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "8.8.8.8:53",
    "protocol": "dns",
    "query": "google.com",
    "timeout": 5
  }'
```

#### Response Example
```json
{
  "target": "8.8.8.8:53",
  "latency_ms": 8.34,
  "remote_addr": "8.8.8.8:53",
  "dns_results": ["142.250.185.78", "142.250.185.46"],
  "response": "DNS query successful",
  "success": true,
  "error": null
}
```

---

### ICMP Test

**Endpoint**: `POST /api/v1/test/icmp`
**Authentication**: Required (JWT or API Key)
**Description**: Execute ICMP test (ping or traceroute)

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target | string | Yes | Hostname or IP to test |
| protocol | string | No | Protocol: ping, traceroute (default: ping) |
| count | integer | No | Number of packets (default: 4) |
| timeout | integer | No | Timeout in seconds (default: 10) |
| packet_size | integer | No | Packet size in bytes (default: 32) |

#### Request Example
```bash
curl -X POST http://localhost:8080/api/v1/test/icmp \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "8.8.8.8",
    "protocol": "ping",
    "count": 4,
    "timeout": 10
  }'
```

#### Response Example
```json
{
  "target": "8.8.8.8",
  "packets_sent": 4,
  "packets_received": 4,
  "packet_loss_percent": 0.0,
  "latency_ms": 12.34,
  "min_latency_ms": 10.12,
  "max_latency_ms": 15.67,
  "jitter_ms": 2.34,
  "std_dev_ms": 1.89,
  "success": true,
  "error": null
}
```

---

## managerServer API

Management backend for authentication and administration.

### Health Check

**Endpoint**: `GET /health`
**Authentication**: None
**Description**: Check server health and version

#### Request Example
```bash
curl http://localhost:5000/health
```

#### Response Example
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Authentication Endpoints

#### Login

**Endpoint**: `POST /api/v1/auth/login`
**Authentication**: None
**Description**: Authenticate user and receive JWT token

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Username |
| password | string | Yes | Password |
| mfa_code | string | Conditional | 6-digit TOTP code (required if MFA enabled) |

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password",
    "mfa_code": "123456"
  }'
```

##### Response Example
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "global_admin",
    "ou_id": null,
    "mfa_enabled": true,
    "api_key": "a1b2c3d4e5f6..."
  },
  "expires_in": 86400
}
```

##### Error Response (MFA Required)
```json
{
  "error": "MFA code required",
  "mfa_required": true
}
```

---

#### Logout

**Endpoint**: `POST /api/v1/auth/logout`
**Authentication**: Required (JWT)
**Description**: Revoke JWT token

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/auth/logout \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "message": "Logged out successfully"
}
```

---

#### Setup MFA

**Endpoint**: `POST /api/v1/auth/mfa/setup`
**Authentication**: Required (JWT)
**Description**: Generate MFA secret and QR code URI

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/auth/mfa/setup \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_uri": "otpauth://totp/WaddlePerf:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=WaddlePerf"
}
```

---

#### Verify MFA

**Endpoint**: `POST /api/v1/auth/mfa/verify`
**Authentication**: Required (JWT)
**Description**: Verify MFA code and enable MFA

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/auth/mfa/verify \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "123456"
  }'
```

##### Response Example
```json
{
  "message": "MFA enabled successfully"
}
```

---

### User Management Endpoints

#### List Users

**Endpoint**: `GET /api/v1/users`
**Authentication**: Required (JWT)
**Description**: List all users with pagination

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| per_page | integer | 50 | Items per page |

##### Request Example
```bash
curl http://localhost:5000/api/v1/users?page=1&per_page=50 \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "global_admin",
      "ou_id": null,
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

---

#### Get User

**Endpoint**: `GET /api/v1/users/<user_id>`
**Authentication**: Required (JWT)
**Description**: Get user details by ID

##### Request Example
```bash
curl http://localhost:5000/api/v1/users/1 \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "global_admin",
  "ou_id": null,
  "mfa_enabled": true,
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

#### Create User

**Endpoint**: `POST /api/v1/users`
**Authentication**: Required (JWT, admin role)
**Description**: Create new user

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Unique username |
| email | string | Yes | Unique email address |
| password | string | Yes | Password (min 8 characters) |
| role | string | No | User role (default: user) |
| ou_id | integer | No | Organization Unit ID |

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "secure_password",
    "role": "user",
    "ou_id": 1
  }'
```

##### Response Example
```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@example.com",
  "role": "user",
  "ou_id": 1,
  "api_key": "a1b2c3d4e5f6...",
  "is_active": true,
  "created_at": "2025-01-15T12:00:00Z"
}
```

---

#### Update User

**Endpoint**: `PUT /api/v1/users/<user_id>`
**Authentication**: Required (JWT)
**Description**: Update user details

##### Request Example
```bash
curl -X PUT http://localhost:5000/api/v1/users/2 \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "updated@example.com",
    "role": "ou_admin",
    "is_active": true
  }'
```

##### Response Example
```json
{
  "id": 2,
  "username": "newuser",
  "email": "updated@example.com",
  "role": "ou_admin",
  "ou_id": 1,
  "is_active": true
}
```

---

#### Change Password

**Endpoint**: `PUT /api/v1/users/<user_id>/password`
**Authentication**: Required (JWT)
**Description**: Change user password

##### Request Example
```bash
curl -X PUT http://localhost:5000/api/v1/users/2/password \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "new_secure_password"
  }'
```

##### Response Example
```json
{
  "message": "Password updated successfully"
}
```

---

#### Delete User

**Endpoint**: `DELETE /api/v1/users/<user_id>`
**Authentication**: Required (JWT, admin role)
**Description**: Delete user

##### Request Example
```bash
curl -X DELETE http://localhost:5000/api/v1/users/2 \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "message": "User deleted successfully"
}
```

---

### Organization Management Endpoints

#### List Organizations

**Endpoint**: `GET /api/v1/organizations`
**Authentication**: Required (JWT)
**Description**: List all organization units

##### Request Example
```bash
curl http://localhost:5000/api/v1/organizations \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "organizations": [
    {
      "id": 1,
      "name": "Engineering",
      "description": "Engineering department",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

#### Get Organization

**Endpoint**: `GET /api/v1/organizations/<org_id>`
**Authentication**: Required (JWT)
**Description**: Get organization details

##### Request Example
```bash
curl http://localhost:5000/api/v1/organizations/1 \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "id": 1,
  "name": "Engineering",
  "description": "Engineering department",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

#### Create Organization

**Endpoint**: `POST /api/v1/organizations`
**Authentication**: Required (JWT, admin role)
**Description**: Create new organization unit

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/organizations \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales",
    "description": "Sales department"
  }'
```

##### Response Example
```json
{
  "id": 2,
  "name": "Sales",
  "description": "Sales department",
  "created_at": "2025-01-15T12:00:00Z"
}
```

---

### Statistics Endpoints

#### Recent Tests

**Endpoint**: `GET /api/v1/statistics/recent`
**Authentication**: Required (JWT)
**Description**: Get recent test results (last 24 hours)

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 100 | Maximum results to return |

##### Request Example
```bash
curl http://localhost:5000/api/v1/statistics/recent?limit=100 \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "results": [
    {
      "id": 123,
      "user_id": 1,
      "username": "admin",
      "device_serial": "laptop-001",
      "device_hostname": "my-laptop",
      "test_type": "http",
      "target_host": "google.com",
      "latency_ms": 45.23,
      "success": true,
      "created_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

---

#### Device Statistics

**Endpoint**: `GET /api/v1/statistics/device/<device_serial>`
**Authentication**: Required (JWT)
**Description**: Get statistics for a specific device

##### Request Example
```bash
curl http://localhost:5000/api/v1/statistics/device/laptop-001 \
  -H "Authorization: Bearer your-jwt-token"
```

##### Response Example
```json
{
  "device": "laptop-001",
  "statistics": [
    {
      "device_serial": "laptop-001",
      "device_hostname": "my-laptop",
      "test_type": "http",
      "total_tests": 150,
      "avg_latency": 42.5,
      "avg_throughput": 3.2,
      "first_test": "2025-01-01T00:00:00Z",
      "last_test": "2025-01-15T14:30:00Z"
    }
  ]
}
```

---

### Results Upload Endpoint

#### Upload Results

**Endpoint**: `POST /api/v1/results/upload`
**Authentication**: Required (JWT or API Key)
**Description**: Upload test results from clients (containerClient, goClient)

##### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| device_serial | string | Yes | Device serial number |
| device_hostname | string | Yes | Device hostname |
| device_os | string | Yes | Operating system |
| device_os_version | string | Yes | OS version |
| test_type | string | Yes | Test type: http, tcp, udp, icmp |
| protocol_detail | string | No | Protocol variant |
| target_host | string | Yes | Target hostname |
| target_ip | string | Yes | Target IP address |
| latency_ms | float | No | Latency in milliseconds |
| throughput_mbps | float | No | Throughput in Mbps |
| jitter_ms | float | No | Jitter in milliseconds |
| packet_loss_percent | float | No | Packet loss percentage |
| raw_results | object | No | Raw test data |

##### Request Example
```bash
curl -X POST http://localhost:5000/api/v1/results/upload \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_serial": "laptop-001",
    "device_hostname": "my-laptop",
    "device_os": "Linux",
    "device_os_version": "6.8.0-86-generic",
    "test_type": "http",
    "protocol_detail": "HTTP/2.0",
    "target_host": "google.com",
    "target_ip": "142.250.185.68",
    "latency_ms": 45.23,
    "throughput_mbps": 3.2,
    "raw_results": {
      "status_code": 200,
      "ttfb_ms": 42.15
    }
  }'
```

##### Response Example
```json
{
  "message": "Results uploaded successfully"
}
```

---

## webClient API

Browser-based testing proxy with WebSocket support.

### Health Check

**Endpoint**: `GET /health`
**Authentication**: None
**Description**: Check server health

#### Request Example
```bash
curl http://localhost:5001/health
```

#### Response Example
```json
{
  "status": "healthy",
  "database": "healthy",
  "auth_enabled": true,
  "timestamp": "2025-01-15T14:30:00Z"
}
```

---

### Authentication Endpoints

#### Login

**Endpoint**: `POST /api/auth/login`
**Authentication**: None
**Description**: Authenticate and create session

##### Request Example
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password"
  }'
```

##### Response Example
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "global_admin"
  },
  "session_id": "a1b2c3d4e5f6..."
}
```

---

#### Logout

**Endpoint**: `POST /api/auth/logout`
**Authentication**: Session
**Description**: Clear session

##### Request Example
```bash
curl -X POST http://localhost:5001/api/auth/logout \
  -H "Cookie: session=your-session-id"
```

##### Response Example
```json
{
  "success": true
}
```

---

#### Auth Status

**Endpoint**: `GET /api/auth/status`
**Authentication**: Session (optional)
**Description**: Check authentication status

##### Request Example
```bash
curl http://localhost:5001/api/auth/status \
  -H "Cookie: session=your-session-id"
```

##### Response Example
```json
{
  "authenticated": true,
  "auth_enabled": true,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "global_admin"
  }
}
```

---

### Test Endpoints

#### Run Test

**Endpoint**: `POST /api/test/<test_type>`
**Authentication**: Required (Session or API Key)
**Description**: Execute network test (proxies to testServer)

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| test_type | string | Test type: http, tcp, udp, icmp |

##### Request Parameters

Same as testServer API for each test type.

##### Request Example
```bash
curl -X POST http://localhost:5001/api/test/http \
  -H "Cookie: session=your-session-id" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://www.google.com",
    "protocol": "auto",
    "timeout": 30
  }'
```

##### Response Example

Same as testServer API response format.

---

### WebSocket API

**Endpoint**: `ws://localhost:5001/socket.io/`
**Protocol**: Socket.IO
**Description**: Real-time test execution with progress updates

#### Connection

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5001', {
  transports: ['websocket']
});

socket.on('connected', (data) => {
  console.log('Connected:', data);
});
```

#### Start Test Event

**Event**: `start_test`
**Description**: Execute test with real-time progress

##### Emit Example
```javascript
socket.emit('start_test', {
  test_type: 'http',
  target: 'https://www.google.com',
  protocol: 'auto',
  timeout: 30,
  count: 10,
  session_id: 'your-session-id',  // or api_key
});
```

#### Test Started Event

**Event**: `test_started`
**Description**: Test execution has begun

##### Receive Example
```javascript
socket.on('test_started', (data) => {
  console.log('Test started:', data);
  // { status: 'started', test_type: 'http' }
});
```

#### Test Progress Event

**Event**: `test_progress`
**Description**: Progress update during test execution

##### Receive Example
```javascript
socket.on('test_progress', (data) => {
  console.log('Progress:', data);
  // { progress: 50, current_index: 5, total: 10 }
});
```

#### Test Complete Event

**Event**: `test_complete`
**Description**: Test execution completed

##### Receive Example
```javascript
socket.on('test_complete', (data) => {
  console.log('Results:', data);
  // Same format as HTTP API response
});
```

#### Error Event

**Event**: `error`
**Description**: Error occurred during test

##### Receive Example
```javascript
socket.on('error', (data) => {
  console.error('Error:', data);
  // { error: 'Error message' }
});
```

---

## Error Responses

All APIs use standard HTTP status codes and return error details in JSON format.

### Error Format

```json
{
  "error": "Error message describing what went wrong",
  "details": "Additional details (optional)"
}
```

### Common Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (authentication required) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (e.g., duplicate username) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Example Error Responses

#### 400 Bad Request
```json
{
  "error": "Missing required fields"
}
```

#### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

#### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

#### 409 Conflict
```json
{
  "error": "Username already exists"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "details": "Database connection failed"
}
```

---

## Rate Limiting

Currently, WaddlePerf does not enforce global rate limits. However, best practices:

- **testServer**: Limit to 100 concurrent tests per instance
- **managerServer**: Recommended 100 requests/minute per user
- **webClient**: Recommended 10 concurrent WebSocket connections per user

Rate limiting can be implemented at the reverse proxy level (nginx, Cloudflare, etc.).

---

## CORS

All APIs support CORS with the following defaults:

**Development**:
- `Access-Control-Allow-Origin: *`

**Production**:
- Configure `CORS_ORIGINS` environment variable with comma-separated origins
- Example: `CORS_ORIGINS=https://example.com,https://www.example.com`

---

## API Versioning

All APIs use version prefixes in the URL path:

- Current version: `/api/v1/`
- Future versions will use `/api/v2/`, `/api/v3/`, etc.
- Old versions will be maintained for at least 6 months after deprecation

---

## SDK Examples

### Python

```python
import requests

# Login
response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['token']

# Run HTTP test
response = requests.post('http://localhost:8080/api/v1/test/http',
    headers={'Authorization': f'Bearer {token}'},
    json={'target': 'https://www.google.com'}
)
print(response.json())
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('http://localhost:5000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'password' })
});
const { token } = await loginResponse.json();

// Run HTTP test
const testResponse = await fetch('http://localhost:8080/api/v1/test/http', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ target: 'https://www.google.com' })
});
const results = await testResponse.json();
console.log(results);
```

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

func main() {
    // Login
    loginData := map[string]string{"username": "admin", "password": "password"}
    loginBody, _ := json.Marshal(loginData)

    resp, _ := http.Post("http://localhost:5000/api/v1/auth/login",
        "application/json", bytes.NewBuffer(loginBody))

    var loginResp map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&loginResp)
    token := loginResp["token"].(string)

    // Run HTTP test
    testData := map[string]string{"target": "https://www.google.com"}
    testBody, _ := json.Marshal(testData)

    req, _ := http.NewRequest("POST", "http://localhost:8080/api/v1/test/http",
        bytes.NewBuffer(testBody))
    req.Header.Set("Authorization", "Bearer "+token)
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    resp, _ = client.Do(req)

    var testResp map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&testResp)
}
```

---

## Support

For API questions or issues:
- GitHub Issues: https://github.com/penguintechinc/WaddlePerf/issues
- Documentation: https://github.com/penguintechinc/WaddlePerf/tree/main/docs

---

**Copyright © 2025 Penguin Technologies Inc.**
