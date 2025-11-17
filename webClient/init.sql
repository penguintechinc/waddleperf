-- WaddlePerf Database Schema for webClient
-- This is a subset of the main schema needed for webClient testing

-- Organization Units table
CREATE TABLE IF NOT EXISTS organization_units (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users table
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

-- Sessions table
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

-- JWT Tokens table
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

-- Server Test Results table
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Client Test Results table
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
-- Password hash generated with bcrypt, cost factor 12
INSERT INTO users (username, email, password_hash, api_key, role, is_active)
VALUES (
    'admin',
    'admin@waddleperf.local',
    '$2b$12$OUa4Ky.uDXNtWEf.sI704uENLZH6XWJ2WHTIW0Ek3JMSIpyqqs576',
    'admin-api-key-abcdef1234567890abcdef1234567890abcdef1234567890ab',
    'global_admin',
    TRUE
) ON DUPLICATE KEY UPDATE username=username;

-- Insert default test user (password: admin123)
-- Password hash generated with bcrypt, cost factor 12
INSERT INTO users (username, email, password_hash, api_key, role, is_active)
VALUES (
    'testuser',
    'test@waddleperf.local',
    '$2b$12$OUa4Ky.uDXNtWEf.sI704uENLZH6XWJ2WHTIW0Ek3JMSIpyqqs576',
    'test-api-key-1234567890abcdef1234567890abcdef1234567890abcdef12',
    'user',
    TRUE
) ON DUPLICATE KEY UPDATE username=username;

-- Clean up expired sessions (optional, for maintenance)
DELETE FROM sessions WHERE expires_at < NOW();
