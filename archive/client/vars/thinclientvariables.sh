# Edit this if on a thin client install
export APP_TITLE="WADDLEPERFCLIENT" # Change this to actual title for Default
export BUILD_THREADS="4"
export RUN_AUTOUPDATES="true"
# IPERF ARGS
export IPERF_URL="https://github.com/esnet/iperf/archive/refs/tags/3.14.tar.gz"

# MTR ARGS
export MTR_VERSION="0.95"
export MTR_ENABLED="true"
export MTR_COMPILE="false"
# HTTPTRACE ARGS
export HTTPTRACE_ENABLED="true"
# PPING ARGS
export PPING_VERSION="0.8.3"
export PPING_ENABLED="true"
#SSHPING ARGS
export SSHPING_ENABLED="true"
# S3
export S3_ENABLED="true"

export APP_TITLE="WADDLEPERF"
# IPERF Environment variables
export IPERF_SERVER_ENABLED="true"
export IPERF_SERVER_IP="127.0.0.1"
export IPERF_SERVER_PORT="5201"
export IPERF_CLIENT_STREAMS="1"
export IPERF_CLIENT_ENABLED="true"
export IPERF_CLIENT_BITRATE="100M"
export IPERF_CLIENT_RETURN="1"
export IPERF_CLIENT_LOGFILE="0"
export IPERF_PASSWORD="changemeplease"
export IPERF_USERNAME="www-data"
export IPERF_PROTOCOL="tcp"
export IPERF_AUTHENTICATION="1"
# NGINX Environment variables
export WEB_PORT="8080"
export WEB_SPORT="443"
export WEB_HOST="localhost"

# S3
export S3_ENABLED="false"
export S3_INTERVAL="10"
export S3_URL="http://localhost"
export S3_BUCKET="changeme"
export S3_ENCRYPT="true"
export S3_COMPATIBILITY="true"
export S3_KEY_ACCESS="key_example_access"
export S3_KEY_SECRET="SUPERSECRETSQUIRREL_EXAMPLE"
# HealthCheck
export HEALTHCHECK_ENABLED="true"
export HEALTHCHECK_INTERVAL="10"

# SSHPING
export SSHPING_COUNT="2"
export SSHPING_TIMEOUT="20"
export SSHPING_DESTHOST="localhost"
export SSHPING_PORT="22"
export SSHPING_USER="ptg-user"
export SSHPING_BANDWIDTH="100M"
# Results drop off location
export RESULTS_DIR="/var/www/waddleperf"
export RESULTS_FILE="results.json"

