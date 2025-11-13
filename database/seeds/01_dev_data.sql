-- Development Seed Data for WaddlePerf
-- WARNING: These are test credentials for development ONLY
-- DO NOT use in production!

USE waddleperf;

-- ============================================
-- Organization Units
-- ============================================
INSERT INTO organization_units (name, description) VALUES
('IT Department', 'Internal IT and infrastructure team'),
('Customer Success', 'Customer-facing support and success team'),
('Engineering', 'Software engineering and development');

-- ============================================
-- Users
-- ============================================
-- Password for all test users: "ChangeMeAlready"
-- bcrypt hash generated with cost factor 12

-- Global Admin user
INSERT INTO users (username, email, password_hash, api_key, role, ou_id, mfa_enabled, is_active) VALUES
('admin', 'admin@waddleperf.local', '$2b$12$9uwyLoVhTeIqjqIKdaigmuJKjjlmoxSS2M293Uks538J2DJZ4Mnf6', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2', 'global_admin', NULL, FALSE, TRUE),

-- Global Reporter user
('reporter', 'reporter@waddleperf.local', '$2b$12$9uwyLoVhTeIqjqIKdaigmuJKjjlmoxSS2M293Uks538J2DJZ4Mnf6', 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3', 'global_reporter', NULL, FALSE, TRUE),

-- OU Admin user (IT Department)
('it_admin', 'it_admin@waddleperf.local', '$2b$12$9uwyLoVhTeIqjqIKdaigmuJKjjlmoxSS2M293Uks538J2DJZ4Mnf6', 'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4', 'ou_admin', 1, FALSE, TRUE),

-- OU Reporter user (Customer Success)
('cs_reporter', 'cs_reporter@waddleperf.local', '$2b$12$9uwyLoVhTeIqjqIKdaigmuJKjjlmoxSS2M293Uks538J2DJZ4Mnf6', 'd4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5', 'ou_reporter', 2, FALSE, TRUE),

-- Regular users
('user1', 'user1@waddleperf.local', '$2b$12$9uwyLoVhTeIqjqIKdaigmuJKjjlmoxSS2M293Uks538J2DJZ4Mnf6', 'e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6', 'user', 3, FALSE, TRUE),
('user2', 'user2@waddleperf.local', '$2b$12$9uwyLoVhTeIqjqIKdaigmuJKjjlmoxSS2M293Uks538J2DJZ4Mnf6', 'f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7', 'user', 3, FALSE, TRUE);

-- ============================================
-- Server Keys
-- ============================================
-- Default dev server key (hashed)
-- Raw key: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
-- Hash: SHA256 of the key
INSERT INTO server_keys (key_hash, description, is_active) VALUES
('9c1185a5c5e9fc54612808977ee8f548b2258d31def617f1b3a3dbc3c1abf5e3', 'Development server key', TRUE);

-- ============================================
-- Sample Client Configs
-- ============================================
INSERT INTO client_configs (user_id, ou_id, config_name, config_data, is_default) VALUES
-- Default config for all users
(NULL, NULL, 'Default Configuration', JSON_OBJECT(
    'tests', JSON_OBJECT(
        'http', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('https://google.com', 'https://cloudflare.com')),
        'tcp', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('8.8.8.8:53')),
        'udp', JSON_OBJECT('enabled', FALSE, 'targets', JSON_ARRAY()),
        'icmp', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('8.8.8.8', '1.1.1.1'))
    ),
    'schedule', JSON_OBJECT('interval_seconds', 300),
    'thresholds', JSON_OBJECT(
        'latency_warning_ms', 100,
        'latency_critical_ms', 500,
        'jitter_warning_ms', 50,
        'jitter_critical_ms', 200,
        'packet_loss_warning_percent', 1.0,
        'packet_loss_critical_percent', 5.0
    )
), TRUE),

-- Engineering OU custom config
(NULL, 3, 'Engineering Config', JSON_OBJECT(
    'tests', JSON_OBJECT(
        'http', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('https://github.com', 'https://gitlab.com', 'https://npm.org')),
        'tcp', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('github.com:22', 'gitlab.com:22')),
        'udp', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('8.8.8.8:53', '1.1.1.1:53')),
        'icmp', JSON_OBJECT('enabled', TRUE, 'targets', JSON_ARRAY('8.8.8.8', '1.1.1.1'))
    ),
    'schedule', JSON_OBJECT('interval_seconds', 120)
), FALSE);

-- ============================================
-- Sample Test Results
-- ============================================

-- Server test results (simulating tests from testServer)
INSERT INTO server_test_results (
    user_id, device_serial, device_hostname, device_os, device_os_version,
    test_type, protocol_detail, target_host, target_ip, client_ip,
    latency_ms, throughput_mbps, jitter_ms, packet_loss_percent,
    raw_results, created_at
) VALUES
-- HTTP tests
(1, 'DEV-001', 'admin-laptop', 'Linux', '6.5.0-ubuntu', 'http', 'http2', 'google.com', '142.250.80.46', '192.168.1.100',
 23.45, 850.5, 2.1, 0.0, JSON_OBJECT('status', 200, 'ttfb_ms', 12.3), DATE_SUB(NOW(), INTERVAL 1 HOUR)),

(1, 'DEV-001', 'admin-laptop', 'Linux', '6.5.0-ubuntu', 'http', 'http2', 'cloudflare.com', '104.16.132.229', '192.168.1.100',
 15.67, 920.3, 1.8, 0.0, JSON_OBJECT('status', 200, 'ttfb_ms', 8.5), DATE_SUB(NOW(), INTERVAL 50 MINUTE)),

-- TCP tests
(5, 'DEV-002', 'user1-desktop', 'Windows', '11', 'tcp', 'raw_tcp', '8.8.8.8', '8.8.8.8', '192.168.1.101',
 12.34, NULL, 3.2, 0.0, JSON_OBJECT('connected', TRUE, 'handshake_ms', 11.2), DATE_SUB(NOW(), INTERVAL 2 HOUR)),

-- ICMP tests
(5, 'DEV-002', 'user1-desktop', 'Windows', '11', 'icmp', 'ping', '8.8.8.8', '8.8.8.8', '192.168.1.101',
 18.92, NULL, 4.5, 0.5, JSON_OBJECT('packets_sent', 10, 'packets_received', 10), DATE_SUB(NOW(), INTERVAL 30 MINUTE)),

(6, 'DEV-003', 'user2-macbook', 'macOS', '14.2', 'icmp', 'ping', '1.1.1.1', '1.1.1.1', '192.168.1.102',
 11.23, NULL, 2.1, 0.0, JSON_OBJECT('packets_sent', 10, 'packets_received', 10), DATE_SUB(NOW(), INTERVAL 15 MINUTE));

-- Client test results (simulating uploads from clients)
INSERT INTO client_test_results (
    user_id, device_serial, device_hostname, device_os, device_os_version,
    test_type, protocol_detail, target_host, target_ip,
    latency_ms, throughput_mbps, jitter_ms, packet_loss_percent,
    raw_results, created_at
) VALUES
-- containerClient tests
(5, 'CONTAINER-001', 'prod-monitor-01', 'Linux', '6.1.0-debian', 'http', 'http2', 'api.example.com', '203.0.113.10',
 45.67, 650.2, 5.3, 0.2, JSON_OBJECT('status', 200), DATE_SUB(NOW(), INTERVAL 10 MINUTE)),

-- goClient tests
(6, 'GO-CLIENT-001', 'user2-macbook', 'macOS', '14.2', 'tcp', 'ssh', 'git.example.com', '198.51.100.20',
 32.15, NULL, 6.8, 0.0, JSON_OBJECT('connected', TRUE, 'ssh_version', 'OpenSSH_9.0'), DATE_SUB(NOW(), INTERVAL 5 MINUTE));

-- ============================================
-- Development Notes
-- ============================================
-- Default credentials for testing:
-- Username: admin
-- Password: ChangeMeAlready
-- API Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
--
-- Server Key (for ENV):
-- MANAGER_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
