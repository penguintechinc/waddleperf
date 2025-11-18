# WaddlePerf Manager Frontend

React + TypeScript frontend for the WaddlePerf managerServer management dashboard.

## Features

- User authentication with JWT and MFA support
- Role-based access control (global_admin, global_reporter, ou_admin, ou_reporter, user)
- User management with CRUD operations
- Organization Unit management
- Test statistics visualization with interactive charts
- User profile with API key display and MFA setup
- Light/dark/auto theme support
- Responsive design for mobile, tablet, and desktop
- Real-time data updates

## Tech Stack

- React 18
- TypeScript
- Vite (build tool)
- React Router DOM (routing)
- Recharts (data visualization)
- Axios (HTTP client)
- QRCode.react (MFA QR codes)

## Prerequisites

- Node.js 18+ (recommended: 20+)
- npm 9+

## Development Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your API URL:
```
VITE_API_URL=http://localhost:5000
```

4. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

## Build Commands

### Development
```bash
npm run dev       # Start dev server with hot reload
```

### Production Build
```bash
npm run build     # Build for production
npm run preview   # Preview production build locally
```

### Linting
```bash
npm run lint      # Run ESLint
```

## Docker Deployment

### Build Docker Image
```bash
docker build -f Dockerfile.frontend -t waddleperf-manager-frontend .
```

### Run Docker Container
```bash
docker run -p 8080:80 waddleperf-manager-frontend
```

The application will be available at `http://localhost:8080`.

### Docker Compose (Recommended)

Create a `docker-compose.yml` in the parent directory:

```yaml
version: '3.8'

services:
  managerserver-api:
    build: ./api
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/waddleperf
    depends_on:
      - db

  managerserver-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "8080:80"
    depends_on:
      - managerserver-api

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=waddleperf
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up -d
```

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: `http://localhost:5000`)

## Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable components
│   │   ├── Navbar.tsx
│   │   ├── Navbar.css
│   │   └── ProtectedRoute.tsx
│   ├── contexts/            # React contexts
│   │   ├── AuthContext.tsx
│   │   └── ThemeContext.tsx
│   ├── pages/               # Page components
│   │   ├── Login.tsx/css
│   │   ├── Dashboard.tsx/css
│   │   ├── Users.tsx/css
│   │   ├── Organizations.tsx/css
│   │   ├── Statistics.tsx/css
│   │   └── Profile.tsx/css
│   ├── services/            # API services
│   │   └── api.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── App.tsx              # Main app component
│   ├── App.css
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── Dockerfile.frontend      # Production Dockerfile
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── package.json
└── README.md
```

## API Integration

The frontend communicates with the managerServer API backend via REST endpoints:

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/mfa/setup` - Setup MFA
- `POST /api/v1/auth/mfa/verify` - Verify MFA
- `GET /api/v1/users` - List users (paginated)
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/:id` - Get user details
- `PUT /api/v1/users/:id` - Update user
- `DELETE /api/v1/users/:id` - Delete user
- `PUT /api/v1/users/:id/password` - Change password
- `GET /api/v1/organizations` - List organizations
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/statistics/recent` - Get recent test results
- `GET /api/v1/statistics/device/:serial` - Get device statistics
- `GET /health` - Health check

## Authentication

The application uses JWT tokens for authentication:

1. User logs in with username/password
2. If MFA is enabled, user provides TOTP code
3. Backend returns JWT token
4. Token is stored in localStorage
5. All subsequent API requests include the token in the `Authorization` header

## Theme System

The application supports three theme modes:

- **Light**: Light theme
- **Dark**: Dark theme
- **Auto**: Automatically switches based on system preference

Theme preference is stored in localStorage and persists across sessions.

## User Roles

- **global_admin**: Full access to all features
- **global_reporter**: Read-only access to all data
- **ou_admin**: Admin access for specific organization unit
- **ou_reporter**: Read-only access for specific organization unit
- **user**: Basic user access, can run tests and view own results

Role-based UI conditionally shows/hides features based on user permissions.

## MFA Setup

1. Navigate to Profile page
2. Click "Enable MFA"
3. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
4. Enter verification code
5. MFA is now enabled

## Development Tips

- Use React DevTools for component debugging
- API calls during development are proxied through Vite dev server
- Hot module replacement (HMR) is enabled for fast development
- TypeScript provides type checking at compile time

## Troubleshooting

### Build Errors

If you encounter build errors, try:
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

### API Connection Issues

1. Verify the API is running at the URL specified in `.env`
2. Check browser console for CORS errors
3. Ensure API endpoints are accessible
4. Verify JWT token is being sent in request headers

### Theme Not Applying

1. Check browser localStorage for `theme` key
2. Clear localStorage and refresh
3. Verify CSS variables are defined in `index.css`

## Contributing

1. Follow existing code style and patterns
2. Use TypeScript for all new files
3. Add proper error handling and loading states
4. Test on multiple browsers and screen sizes
5. Update this README if adding new features

## License

Copyright (c) 2024 Penguin Technologies Inc.

## Support

For issues and questions, please open an issue at the GitHub repository.
