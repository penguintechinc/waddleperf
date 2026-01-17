#!/bin/sh
# Runtime configuration injection for WaddlePerf webClient
# This script generates config.js from environment variables at container startup

# Default values
API_URL="${VITE_API_URL:-https://waddleperf.penguintech.io}"
TESTSERVER_URL="${VITE_TESTSERVER_URL:-https://testserver.waddleperf.penguintech.io}"

# Derive WebSocket URL from API URL
WS_URL=$(echo "${API_URL}" | sed 's/^http/ws/')

# Generate runtime config file
cat > /usr/share/nginx/html/config.js << EOF
// Runtime configuration - generated at container startup
// DO NOT EDIT - this file is regenerated on every container start
window.__CONFIG__ = {
  API_URL: "${API_URL}",
  WS_URL: "${WS_URL}",
  TESTSERVER_URL: "${TESTSERVER_URL}"
};
console.log('[Config] Runtime configuration loaded:', window.__CONFIG__);
EOF

echo "Generated runtime config:"
echo "  API_URL=${API_URL}"
echo "  WS_URL=${WS_URL}"
echo "  TESTSERVER_URL=${TESTSERVER_URL}"

# Start nginx
exec nginx -g 'daemon off;'
