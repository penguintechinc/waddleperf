# Development Standards - WaddlePerf

Comprehensive development standards for WaddlePerf project, aligned with Penguin Tech Inc template standards.

## Table of Contents

1. [Language Selection Criteria](#language-selection-criteria)
2. [Flask-Security-Too Integration](#flask-security-too-integration)
3. [ReactJS Frontend Standards](#reactjs-frontend-standards)
4. [Database Standards](#database-standards)
5. [Protocol Support](#protocol-support)
6. [API Versioning](#api-versioning)
7. [Performance Best Practices](#performance-best-practices)
8. [High-Performance Networking](#high-performance-networking)
9. [Microservices Architecture](#microservices-architecture)
10. [Docker Standards](#docker-standards)
11. [Testing Requirements](#testing-requirements)
12. [Security Standards](#security-standards)
13. [Documentation Standards](#documentation-standards)
14. [Web UI Design Standards](#web-ui-design-standards)
15. [CI/CD Standards](#cicd-standards)

---

## Language Selection Criteria

**WaddlePerf uses a case-by-case basis evaluation:**

### Python 3.13 (Primary for Backend Services)
**Use Python for:**
- Flask REST API server
- Client-side test runners
- Data processing and result aggregation
- Integration services
- Admin tools and utilities

**Advantages:**
- Rapid development and iteration
- Rich ecosystem for testing tools
- Excellent async support for I/O-bound operations
- Easy maintenance and debugging

### Go 1.23.x (Performance-Critical Clients)
**Use Go for:**
- Native desktop clients
- High-performance test tools
- CLI utilities requiring minimal dependencies
- Multi-platform binary distribution

**Decision Matrix:**
- < 10K req/sec: Python 3.13
- Network-intensive native clients: Go 1.23.x
- Multi-platform binaries needed: Go 1.23.x

---

## Flask-Security-Too Integration

**MANDATORY for ALL Flask applications in WaddlePerf**

### Core Features Required
- User authentication and session management
- Role-based access control (RBAC): Admin, Maintainer, Viewer
- Password hashing with bcrypt
- Email confirmation and password reset
- Token-based authentication for APIs
- Login tracking and session management

### Integration Pattern with PyDAL

```python
from flask import Flask
from flask_security import Security, auth_required
from pydal import DAL, Field

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'

# PyDAL database
db = DAL(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
         f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
         pool_size=10, migrate=True)

# Define tables
db.define_table('auth_user',
    Field('email', 'string', unique=True),
    Field('password', 'string'),
    Field('active', 'boolean', default=True),
    Field('fs_uniquifier', 'string', unique=True))

db.define_table('auth_role',
    Field('name', 'string', unique=True),
    Field('description', 'text'))

# Flask-Security-Too setup
from flask_security import PyDALUserDatastore
user_datastore = PyDALUserDatastore(db, db.auth_user, db.auth_role)
security = Security(app, user_datastore)

@app.route('/api/v1/protected')
@auth_required()
def protected_endpoint():
    return {'message': 'Access granted'}
```

### Default Roles in WaddlePerf
| Role | Permissions |
|------|-------------|
| **Admin** | Full access: user CRUD, test configuration, all features |
| **Maintainer** | Read/write test results, manage test schedules |
| **Viewer** | Read-only access to results and dashboards |

---

## ReactJS Frontend Standards

**ALL frontend applications in WaddlePerf MUST use ReactJS**

### Project Structure

```
services/webui/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components (Dashboard, Tests, Results)
│   ├── services/        # API client services
│   ├── hooks/           # Custom React hooks
│   ├── context/         # Auth and theme context
│   ├── utils/           # Utility functions
│   ├── App.jsx
│   └── index.jsx
├── package.json
├── tailwind.config.js
└── Dockerfile
```

### Design Standards

**Dark Theme + Gold Text Default:**
- Background: slate-900 (#0f172a)
- Primary text: amber-400 (gold)
- Interactive elements: sky-blue accent
- Use Tailwind CSS v4 with custom theme

### Component Examples

**Sidebar Navigation** (Elder Pattern):
```jsx
<div className="fixed inset-y-0 left-0 w-64 bg-slate-800 border-r border-slate-700">
  {/* Navigation items with collapsible categories */}
</div>
```

**Tab Navigation** (WaddlePerf Pattern):
```jsx
<div className="flex gap-4 border-b border-slate-700 mb-6">
  {tabs.map(tab => (
    <button
      className={`tab-button ${activeTab === tab ? 'active' : ''}`}
      onClick={() => setActiveTab(tab)}
    >
      {tab.label}
    </button>
  ))}
</div>
```

---

## Database Standards

### Hybrid Approach: SQLAlchemy + PyDAL

**Initialization Phase (SQLAlchemy):**
- Schema creation
- Migration management
- Initial table setup

**Day-to-Day Operations (PyDAL):**
- All CRUD operations
- Query building
- Transaction management

### Environment Variables

WaddlePerf applications MUST accept:
- `DB_TYPE`: `postgres`, `mysql`, or `sqlite`
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASS`: Database password
- `DB_POOL_SIZE`: Connection pool size (default: 10)

### MariaDB Galera Requirements

See [CLAUDE.md](../CLAUDE.md#mariadb-galera-cluster-requirements) for comprehensive Galera cluster requirements.

**Critical Points for WaddlePerf:**
1. ALL tables MUST have primary keys
2. Use InnoDB only
3. Keep transactions short
4. Avoid hot-spot updates
5. Test with multiple nodes

---

## Protocol Support

**WaddlePerf applications MUST support multiple communication protocols:**

### Required Protocols
1. **REST API**: Standard `/api/v1/endpoint` format
2. **gRPC**: For high-performance inter-service communication
3. **HTTP/1.1, HTTP/2, HTTP/3 (QUIC)**: Modern protocol support

### Environment Variables
- `HTTP1_ENABLED`: Enable HTTP/1.1 (default: true)
- `HTTP2_ENABLED`: Enable HTTP/2 (default: true)
- `HTTP3_ENABLED`: Enable HTTP/3/QUIC (default: false)
- `GRPC_ENABLED`: Enable gRPC (default: true)
- `HTTP_PORT`: REST API port (default: 8080)
- `GRPC_PORT`: gRPC port (default: 50051)

---

## API Versioning

**MANDATORY: ALL REST APIs use `/api/v{major}/endpoint` format**

### Version Strategy
- **Current Version**: Fully supported
- **Previous Version (N-1)**: Bug fixes and security patches only
- **Older Versions**: Deprecated with sunset headers

### WaddlePerf API Endpoints

**v1 Endpoints:**
- `/api/v1/tests` - Test management
- `/api/v1/results` - Test results
- `/api/v1/auth/login` - Authentication
- `/api/v1/health` - Health check

### Deprecation Pattern

```python
@app.route('/api/v1/tests')
def get_tests_v1():
    response = make_response(jsonify(tests))
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = 'Sun, 01 Jan 2026 00:00:00 GMT'
    response.headers['Link'] = '</api/v2/tests>; rel="successor-version"'
    return response
```

---

## Performance Best Practices

### Python Performance

**Concurrency Patterns:**
- **asyncio**: I/O-bound operations (network, database)
- **threading**: Blocking I/O with legacy libraries
- **multiprocessing**: CPU-bound operations

**Dataclasses with Slots (MANDATORY):**
```python
from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class TestResult:
    """30-50% memory reduction with slots"""
    id: int
    timestamp: str
    latency: float
    packet_loss: float
```

**Type Hints (MANDATORY):**
```python
from typing import List, Optional

async def run_tests(
    test_ids: List[int],
    timeout: int = 30,
    callback: Optional[Callable] = None
) -> Dict[int, TestResult]:
    """Full type hints required"""
    pass
```

### Go Performance

- Goroutines for concurrent operations
- Sync primitives for shared data
- Context for cancellation and timeouts
- Avoid allocations in hot paths

---

## High-Performance Networking

**For WaddlePerf network testing components:**

### When to Use XDP/AF_XDP

**Traffic Thresholds:**
- Standard networking: < 100K packets/sec
- XDP consideration: 100K - 500K packets/sec
- AF_XDP required: > 500K packets/sec

### Use Cases for WaddlePerf
- Kernel-level packet filtering
- Zero-copy packet capture
- Ultra-low latency test protocols
- High-frequency performance sampling

---

## Microservices Architecture

**WaddlePerf uses microservices pattern:**

### Service Breakdown
1. **API Backend** (Flask): Test orchestration, result storage, user management
2. **Web UI** (React): Dashboard, test configuration, result visualization
3. **Test Clients** (Python/Go): Test execution, data collection
4. **Database** (MariaDB): Persistent data storage

### Communication Patterns
- **Synchronous**: REST API, gRPC
- **Asynchronous**: Message queues (future enhancement)
- **Service Discovery**: Docker networking

---

## Docker Standards

### Base Image Selection for WaddlePerf

**Python Services:**
- Build/runtime: `python:3.13-slim` (Debian-based)
- Rationale: Better compatibility, faster builds than Alpine

**Go Services:**
- Build stage: `golang:1.23-bookworm`
- Runtime stage: `alpine:3.19` (minimal static binaries)

**Frontend:**
- Build: `node:18-alpine`
- Runtime: `nginx:alpine`

### Multi-Stage Build Example

```dockerfile
FROM golang:1.23-bookworm AS builder
WORKDIR /build
COPY . .
RUN CGO_ENABLED=0 go build -o waddleperf-client ./cmd/client

FROM alpine:3.19
COPY --from=builder /build/waddleperf-client /usr/local/bin/
CMD ["waddleperf-client"]
```

### Docker Compose Standards

**Always create `docker-compose.dev.yml` for local development**

```yaml
version: '3.8'

services:
  api:
    build: ./services/api
    environment:
      - DB_TYPE=postgres
      - DB_HOST=postgres
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=devpassword
      - POSTGRES_DB=waddleperf
```

---

## Testing Requirements

### Unit Testing

**All code must have comprehensive unit tests:**
- Network isolation: NO external API/database calls
- Mock all dependencies
- Minimum 70% code coverage for new code
- Use table-driven tests for edge cases

### Integration Testing

- Component interactions verified
- Test databases and services
- API contract verification
- Authentication and authorization

### E2E Testing

- Critical workflows only
- Staging environment
- Full system integration verification

---

## Security Standards

### Input Validation

- ALL inputs MUST have validators
- Use shared libraries for consistency
- Server-side validation mandatory
- XSS and SQL injection prevention

### Authentication & Authorization

- Multi-factor authentication support
- Role-based access control (RBAC)
- JWT token validation
- Secure session cookies

### TLS/Encryption

- TLS 1.2 minimum, prefer TLS 1.3
- HTTPS for all external communication
- Password hashing: Argon2id (Python)
- AES-256-GCM for sensitive data

### Dependency Security

- Regular security audits
- No HIGH or CRITICAL vulnerabilities
- Pin security-critical versions
- Monitor via Dependabot and Socket.dev

---

## Documentation Standards

### README.md

- Project overview
- Quick start guide
- Contributing guidelines
- License information
- Links to detailed docs

### docs/ Folder Structure

```
docs/
├── STANDARDS.md         # This file
├── WORKFLOWS.md         # CI/CD pipeline
├── ARCHITECTURE.md      # System design
├── DATABASE.md          # Database schema and Galera
├── API.md              # API reference
├── INSTALLATION.md     # Setup guide
├── USAGE.md            # User guide
├── SECURITY.md         # Security policies
└── RELEASE_NOTES.md    # Version history
```

### Code Documentation

**Go packages:**
- Package-level comments
- Function comments for exported functions
- Example code for complex functions

**Python modules:**
- Module docstrings (PEP 257)
- Function/class docstrings with type hints
- Complex logic comments explaining WHY

---

## Web UI Design Standards

### Design Philosophy

- **Dark Theme Default**: Reduced eye strain
- **Consistent Spacing**: Tailwind spacing utilities
- **Smooth Transitions**: 200ms ease transitions
- **Responsive Design**: Mobile-first approach

### Color Palette (WaddlePerf)

```css
:root {
  /* Backgrounds */
  --bg-primary: #0f172a;      /* slate-900 */
  --bg-secondary: #1e293b;    /* slate-800 */

  /* Text - Gold theme */
  --text-primary: #fbbf24;    /* amber-400 */
  --text-secondary: #f59e0b;  /* amber-500 */

  /* Accents */
  --primary-500: #0ea5e9;     /* sky-blue */
  --primary-600: #0284c7;     /* sky-blue */
}
```

### Navigation Patterns

**Sidebar (Elder Pattern):**
- Fixed left edge, full height
- Collapsible categories
- Active route highlighting
- Admin items with yellow accent

**Tabs (WaddlePerf Pattern):**
- Horizontal tab navigation
- Underline active tab
- Smooth color transitions
- Gold text, blue underline when active

---

## CI/CD Standards

### Workflow Requirements

**All workflows MUST include:**
1. `.version` path filters
2. Version detection steps
3. Epoch64 timestamp generation
4. Security scanning (gosec for Go)
5. Multi-platform Docker builds
6. Artifact upload with retention

### Build Naming

**Regular builds (no version change):**
- Main: `{service}:beta-{epoch64}`
- Feature: `{service}:alpha-{epoch64}`

**Version releases (.version changed):**
- Main: `{service}:v{X.Y.Z}-beta`
- Feature: `{service}:v{X.Y.Z}-alpha`
- Release: `{service}:v{X.Y.Z}` + `latest`

### Security Scanning

**Go (gosec):**
```bash
gosec -fmt json -out results.json ./...
```

**Python (bandit):**
```bash
bandit -r services/flask-backend -f json -o bandit-report.json
```

**All projects: Trivy container scanning**

---

## Quality Checklist

Before completing any task:

- All error cases handled properly
- Unit tests cover all code paths
- Integration tests verify interactions
- Security requirements implemented
- Performance meets standards
- Documentation complete and accurate
- Code review standards met
- No hardcoded secrets/credentials
- Logging and monitoring in place
- Build passes in containerized environment
- No security vulnerabilities
- Edge cases tested

---

**Document Version**: 2.0 (Updated to template standards)
**Last Updated**: 2025-12-18
**Maintained by**: Penguin Tech Inc
