FROM ghcr.io/penguincloud/core:main
LABEL company="Penguin Tech Group LLC"
LABEL org.opencontainers.image.authors="info@penguintech.io"
LABEL license="GNU AGPL3"
# GET THE FILES WHERE WE NEED THEM!
COPY . /opt/manager/

WORKDIR /opt/manager
RUN apt update 
# PUT YER ARGS in here
ARG APP_TITLE="WADDLEPERF" # Change this to actual title for Default
ARG BUILD_THREADS="4"
ARG RUN_AUTOUPDATES="true"
ARG AUTOPERF_ENABLED="true"
ARG AUTOPERF_INTERVAL="5"
# IPERF ARGS
ARG IPERF_URL="https://github.com/esnet/iperf/archive/refs/tags/3.14.tar.gz"

# MTR ARGS
ARG MTR_VERSION="0.95"
ARG MTR_ENABLED="true"
ARG MTR_COMPILE="false"
# HTTPTRACE ARGS
ARG HTTPTRACE_ENABLED="true"
# PPING ARGS
ARG PPING_VERSION="0.8.3"
ARG PPING_ENABLED="true"
#SSHPING ARGS
ARG SSHPING_ENABLED="true"
# S3
ARG S3_ENABLED="true"

# BUILD IT!
RUN ansible-playbook entrypoint.yml -c local --tags build
#------------------------------------------------------------------#
# General Environment variables
ENV APP_TITLE="WADDLEPERF"
ENV RUN_MODE="docker"
# IPERF Environment variables
ENV IPERF_SERVER_IP="127.0.0.1"
ENV IPERF_SERVER_PORT="5201"
ENV IPERF_CLIENT_STREAMS="1"
ENV IPERF_CLIENT_BITRATE="100M"
ENV IPERF_CLIENT_RETURN="1"
ENV IPERF_CLIENT_LOGFILE="0"
ENV IPERF_PASSWORD="changemeplease"
ENV IPERF_USERNAME="www-data"
ENV IPERF_PROTOCOL="tcp"
ENV IPERF_AUTHENTICATION="1"
# NGINX Environment variables
ENV WEB_PORT="8080"
ENV WEB_SPORT="443"
ENV WEB_HOST="localhost"
# MTR Environment variables - ICMP, UDP, and TCP Ping Tool Suite
ENV MTR_ENABLED="true"
ENV MTR_USE4="true"
ENV MTR_USE6="false"
ENV MTR_LOCALPORT="4343"
ENV MTR_DESTPORT="9090"
ENV MTR_DESTHOST="127.0.0.1"
ENV MTR_PACKET_SIZE="1450"
ENV MTR_PACKET_COUNT="2"
ENV MTR_PACKET_INTERVAL="2"
ENV MTR_PACKET_PROTOCOL="icmp"
ENV MTR_PACKET_TOS="0000"
ENV MTR_LOOKUPS_DNS="true"
ENV MTR_LOOKUPS_IPINFO="true"
ENV MTR_LOOKUPS_ASNINFO="true"
# PPING - HTTP, QUIC, DNS, and TLS Ping Tool Suite
ENV PPING_ENABLED="true"
ENV PPING_PROTOCOL="http"
ENV PPING_COUNT="2"
ENV PPING_INTERVAL="2"
ENV PPING_USE4="false"
ENV PPING_USE6="false"
ENV PPING_DESTPORT="9090"
ENV PPING_DESTHOST="localhost"
# HTTPTRACE
ENV HTTPTRACE_ENABLED="true"
ENV HTTPTRACE_URL="http://localhost"
# S3
ENV S3_ENABLED="false"
ENV S3_INTERVAL="10"
ENV S3_URL="http://localhost"
ENV S3_BUCKET="changeme"
ENV S3_ENCRYPT="true"
ENV S3_COMPATIBILITY="true"
ENV S3_KEY_ACCESS="key_example_access"
ENV S3_KEY_SECRET="SUPERSECRETSQUIRREL_EXAMPLE"
# HealthCheck
ENV HEALTHCHECK_ENABLED="true"
ENV HEALTHCHECK_INTERVAL="10"
# Automatic Performance Testing for Client
ENV AUTOPERF_ENABLED="true"
ENV AUTOPERF_INTERVAL="10"
# SSHPING
ENV SSHPING_ENABLED="true"
ENV SSHPING_COUNT="2"
ENV SSHPING_TIMEOUT="20"
ENV SSHPING_DESTHOST="localhost"
ENV SSHPING_PORT="22"
ENV SSHPING_USER="ptg-user"
ENV SSHPING_BANDWIDTH="100M"
# Results drop off location
ENV RESULTS_DIR="/var/www/waddleperf"
ENV RESULTS_FILE="results.json"

# Switch to non-root user
USER www-data
# Entrypoint time (aka runtime)
ENTRYPOINT ["/bin/bash","/opt/manager/client.sh"]
