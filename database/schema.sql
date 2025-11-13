-- WaddlePerf Database Schema
-- MariaDB Galera Cluster - ONLY persistence and state holder

-- Set character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS waddleperf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE waddleperf;

-- ============================================
-- Organization Units Table
-- ============================================
CREATE TABLE IF NOT EXISTS organization_units (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    role ENUM('global_admin', 'global_reporter', 'ou_admin', 'ou_reporter', 'user') NOT NULL DEFAULT 'user',
    ou_id INT NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(32) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_api_key (api_key),
    INDEX idx_ou_id (ou_id),
    FOREIGN KEY (ou_id) REFERENCES organization_units(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Sessions Table
-- Stores all session state for stateless servers
-- ============================================
CREATE TABLE IF NOT EXISTS sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    data JSON NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- JWT Tokens Table
-- ============================================
CREATE TABLE IF NOT EXISTS jwt_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Server Keys Table
-- 64-character shared keys for server-to-server authentication
-- ============================================
CREATE TABLE IF NOT EXISTS server_keys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    description VARCHAR(255) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_key_hash (key_hash),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Server Test Results Table
-- Results from tests executed by testServer (when clients connect to it)
-- ============================================
CREATE TABLE IF NOT EXISTS server_test_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    device_serial VARCHAR(255) NOT NULL,
    device_hostname VARCHAR(255) NOT NULL,
    device_os VARCHAR(100) NOT NULL,
    device_os_version VARCHAR(100) NOT NULL,

    test_type ENUM('http', 'tcp', 'udp', 'icmp') NOT NULL,
    protocol_detail VARCHAR(50) NULL,

    target_host VARCHAR(255) NOT NULL,
    target_ip VARCHAR(45) NOT NULL,
    client_ip VARCHAR(45) NOT NULL,

    latency_ms DECIMAL(10,4) NULL,
    throughput_mbps DECIMAL(12,4) NULL,
    jitter_ms DECIMAL(10,4) NULL,
    packet_loss_percent DECIMAL(5,2) NULL,

    raw_results JSON NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_device_serial (device_serial),
    INDEX idx_test_type (test_type),
    INDEX idx_created_at (created_at),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_device_test (device_serial, test_type, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Client Test Results Table
-- Results uploaded by clients (containerClient, goClient, webClient)
-- ============================================
CREATE TABLE IF NOT EXISTS client_test_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    device_serial VARCHAR(255) NOT NULL,
    device_hostname VARCHAR(255) NOT NULL,
    device_os VARCHAR(100) NOT NULL,
    device_os_version VARCHAR(100) NOT NULL,

    test_type ENUM('http', 'tcp', 'udp', 'icmp') NOT NULL,
    protocol_detail VARCHAR(50) NULL,

    target_host VARCHAR(255) NOT NULL,
    target_ip VARCHAR(45) NOT NULL,

    latency_ms DECIMAL(10,4) NULL,
    throughput_mbps DECIMAL(12,4) NULL,
    jitter_ms DECIMAL(10,4) NULL,
    packet_loss_percent DECIMAL(5,2) NULL,

    raw_results JSON NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_device_serial (device_serial),
    INDEX idx_test_type (test_type),
    INDEX idx_created_at (created_at),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_device_test (device_serial, test_type, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Client Configs Table
-- Configuration pushed to clients from managerServer
-- ============================================
CREATE TABLE IF NOT EXISTS client_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    ou_id INT NULL,
    config_name VARCHAR(255) NOT NULL,
    config_data JSON NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_ou_id (ou_id),
    INDEX idx_is_default (is_default),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ou_id) REFERENCES organization_units(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Partitioning for test_results tables (by date)
-- Partition by RANGE on created_at for better query performance
-- ============================================
-- Note: Partitioning is commented out for initial setup
-- Uncomment and adjust as needed for production

/*
ALTER TABLE server_test_results PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p_2024_01 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01 00:00:00')),
    PARTITION p_2024_02 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01 00:00:00')),
    PARTITION p_2024_03 VALUES LESS THAN (UNIX_TIMESTAMP('2024-04-01 00:00:00')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

ALTER TABLE client_test_results PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p_2024_01 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01 00:00:00')),
    PARTITION p_2024_02 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01 00:00:00')),
    PARTITION p_2024_03 VALUES LESS THAN (UNIX_TIMESTAMP('2024-04-01 00:00:00')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
*/

-- ============================================
-- Views for common queries
-- ============================================

-- View: Recent test results (last 24 hours)
CREATE OR REPLACE VIEW v_recent_server_tests AS
SELECT
    str.id,
    str.user_id,
    str.device_serial,
    str.device_hostname,
    str.device_os,
    str.device_os_version,
    str.test_type,
    str.protocol_detail,
    str.target_host,
    str.target_ip,
    str.latency_ms,
    str.throughput_mbps,
    str.jitter_ms,
    str.packet_loss_percent,
    str.raw_results,
    str.created_at,
    u.username,
    u.email,
    ou.name AS organization_name
FROM server_test_results str
LEFT JOIN users u ON str.user_id = u.id
LEFT JOIN organization_units ou ON u.ou_id = ou.id
WHERE str.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY str.created_at DESC;

CREATE OR REPLACE VIEW v_recent_client_tests AS
SELECT
    ctr.id,
    ctr.user_id,
    ctr.device_serial,
    ctr.device_hostname,
    ctr.device_os,
    ctr.device_os_version,
    ctr.test_type,
    ctr.protocol_detail,
    ctr.target_host,
    ctr.target_ip,
    ctr.latency_ms,
    ctr.throughput_mbps,
    ctr.jitter_ms,
    ctr.packet_loss_percent,
    ctr.raw_results,
    ctr.created_at,
    u.username,
    u.email,
    ou.name AS organization_name
FROM client_test_results ctr
LEFT JOIN users u ON ctr.user_id = u.id
LEFT JOIN organization_units ou ON u.ou_id = ou.id
WHERE ctr.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY ctr.created_at DESC;

-- View: Test statistics by device
CREATE OR REPLACE VIEW v_device_test_stats AS
SELECT
    device_serial,
    device_hostname,
    test_type,
    COUNT(*) AS total_tests,
    AVG(latency_ms) AS avg_latency,
    AVG(throughput_mbps) AS avg_throughput,
    AVG(jitter_ms) AS avg_jitter,
    AVG(packet_loss_percent) AS avg_packet_loss,
    MIN(created_at) AS first_test,
    MAX(created_at) AS last_test
FROM (
    SELECT device_serial, device_hostname, test_type, latency_ms, throughput_mbps, jitter_ms, packet_loss_percent, created_at FROM server_test_results
    UNION ALL
    SELECT device_serial, device_hostname, test_type, latency_ms, throughput_mbps, jitter_ms, packet_loss_percent, created_at FROM client_test_results
) AS all_tests
GROUP BY device_serial, device_hostname, test_type;

-- ============================================
-- Cleanup Procedures
-- ============================================

-- Procedure: Clean up expired sessions
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS sp_cleanup_expired_sessions()
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
END$$
DELIMITER ;

-- Procedure: Clean up expired JWT tokens
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS sp_cleanup_expired_tokens()
BEGIN
    DELETE FROM jwt_tokens WHERE expires_at < NOW() OR revoked = TRUE;
END$$
DELIMITER ;

-- Procedure: Archive old test results (older than 90 days)
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS sp_archive_old_tests(IN days_to_keep INT)
BEGIN
    -- This would typically move data to an archive table
    -- For now, just delete old records
    DELETE FROM server_test_results
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);

    DELETE FROM client_test_results
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
END$$
DELIMITER ;

-- ============================================
-- Scheduled Events (optional, for automatic cleanup)
-- ============================================
-- Note: Requires event_scheduler to be enabled
-- SET GLOBAL event_scheduler = ON;

/*
CREATE EVENT IF NOT EXISTS ev_cleanup_sessions
ON SCHEDULE EVERY 1 HOUR
DO CALL sp_cleanup_expired_sessions();

CREATE EVENT IF NOT EXISTS ev_cleanup_tokens
ON SCHEDULE EVERY 1 HOUR
DO CALL sp_cleanup_expired_tokens();

CREATE EVENT IF NOT EXISTS ev_archive_tests
ON SCHEDULE EVERY 1 DAY
DO CALL sp_archive_old_tests(90);
*/

-- ============================================
-- Initial Data / Seed Data
-- ============================================
-- See database/seeds/ directory for seed data SQL scripts
