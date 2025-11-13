-- WaddlePerf Database Migration
-- Add System Configuration and OU Enrollment Tokens
-- Similar to FleetDM teams with enrollment tokens

USE waddleperf;

-- ============================================
-- System Configuration Table
-- Global settings for the WaddlePerf system
-- ============================================
CREATE TABLE IF NOT EXISTS system_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NULL,
    config_type ENUM('string', 'boolean', 'integer', 'json') NOT NULL DEFAULT 'string',
    description TEXT NULL,
    updated_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key),
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- OU Enrollment Secrets Table
-- Secrets used for MDM-style device enrollment (FleetDM-style)
-- Multiple secrets per OU for rotation support
-- ============================================
CREATE TABLE IF NOT EXISTS ou_enrollment_secrets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ou_id INT NOT NULL,
    secret VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(255) NULL COMMENT 'Human-readable name for this secret',
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ou_id (ou_id),
    INDEX idx_secret (secret),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (ou_id) REFERENCES organization_units(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Device Enrollments Table
-- Track which devices are enrolled and their OU assignment
-- Like FleetDM: once enrolled to an OU, device stays in that OU
-- ============================================
CREATE TABLE IF NOT EXISTS device_enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ou_id INT NOT NULL COMMENT 'OU the device belongs to (permanent after enrollment)',
    enrollment_secret_id INT NOT NULL COMMENT 'Secret used during enrollment',
    device_serial VARCHAR(255) UNIQUE NOT NULL,
    device_hostname VARCHAR(255) NOT NULL,
    device_os VARCHAR(100) NOT NULL,
    device_os_version VARCHAR(100) NOT NULL,
    client_type ENUM('containerClient', 'goClient', 'webClient') NOT NULL,
    client_version VARCHAR(50) NULL,
    enrolled_ip VARCHAR(45) NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_ou_id (ou_id),
    INDEX idx_secret_id (enrollment_secret_id),
    INDEX idx_device_serial (device_serial),
    INDEX idx_last_seen (last_seen),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (ou_id) REFERENCES organization_units(id) ON DELETE CASCADE,
    FOREIGN KEY (enrollment_secret_id) REFERENCES ou_enrollment_secrets(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Insert Default System Configuration
-- ============================================
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
-- MFA Settings
('mfa_required_global', 'false', 'boolean', 'Require MFA for all users globally'),
('mfa_required_admins', 'false', 'boolean', 'Require MFA for admin users only'),

-- Default Test Configuration for containerClient and goClient
('default_tests_enabled', '{"http": true, "tcp": true, "udp": true, "icmp": true}', 'json', 'Default enabled tests for auto-enrollment'),
('default_test_targets', '{
  "http": ["https://google.com", "https://cloudflare.com"],
  "tcp": ["8.8.8.8:53", "1.1.1.1:53"],
  "udp": ["8.8.8.8:53", "1.1.1.1:53"],
  "icmp": ["8.8.8.8", "1.1.1.1"]
}', 'json', 'Default test targets for auto-enrollment'),
('default_test_interval_seconds', '300', 'integer', 'Default test interval in seconds (5 minutes)'),

-- Test Thresholds
('default_latency_warning_ms', '100', 'integer', 'Default latency warning threshold in milliseconds'),
('default_latency_critical_ms', '500', 'integer', 'Default latency critical threshold in milliseconds'),
('default_jitter_warning_ms', '50', 'integer', 'Default jitter warning threshold in milliseconds'),
('default_jitter_critical_ms', '200', 'integer', 'Default jitter critical threshold in milliseconds'),
('default_packet_loss_warning_percent', '1.0', 'string', 'Default packet loss warning threshold percentage'),
('default_packet_loss_critical_percent', '5.0', 'string', 'Default packet loss critical threshold percentage'),

-- Client Settings
('client_auto_update_enabled', 'true', 'boolean', 'Enable automatic client configuration updates'),
('client_check_in_interval_seconds', '60', 'integer', 'Client check-in interval for config updates'),

-- Data Retention
('test_results_retention_days', '90', 'integer', 'Number of days to retain test results before archiving'),
('session_max_age_hours', '24', 'integer', 'Maximum session age in hours'),
('jwt_token_expiry_hours', '168', 'integer', 'JWT token expiry in hours (7 days)')

ON DUPLICATE KEY UPDATE config_value=VALUES(config_value);

-- ============================================
-- View: Active Enrollment Secrets by OU
-- ============================================
CREATE OR REPLACE VIEW v_active_enrollment_secrets AS
SELECT
    oes.id,
    oes.secret,
    oes.name,
    oes.created_at,
    ou.id AS ou_id,
    ou.name AS ou_name,
    ou.description AS ou_description,
    u.username AS created_by_username,
    COUNT(de.id) AS enrolled_device_count
FROM ou_enrollment_secrets oes
INNER JOIN organization_units ou ON oes.ou_id = ou.id
LEFT JOIN users u ON oes.created_by = u.id
LEFT JOIN device_enrollments de ON oes.id = de.enrollment_secret_id
WHERE oes.is_active = TRUE
GROUP BY oes.id, oes.secret, oes.name, oes.created_at, ou.id, ou.name, ou.description, u.username;

-- ============================================
-- View: Device Enrollment Status
-- ============================================
CREATE OR REPLACE VIEW v_device_enrollments AS
SELECT
    de.id,
    de.device_serial,
    de.device_hostname,
    de.device_os,
    de.device_os_version,
    de.client_type,
    de.client_version,
    de.enrolled_ip,
    de.enrolled_at,
    de.last_seen,
    de.is_active,
    ou.id AS ou_id,
    ou.name AS ou_name,
    oes.name AS enrollment_secret_name
FROM device_enrollments de
INNER JOIN organization_units ou ON de.ou_id = ou.id
INNER JOIN ou_enrollment_secrets oes ON de.enrollment_secret_id = oes.id;

-- ============================================
-- Stored Procedures
-- ============================================

-- Procedure: Enroll a device with a secret (FleetDM-style)
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS sp_enroll_device(
    IN p_secret VARCHAR(128),
    IN p_device_serial VARCHAR(255),
    IN p_device_hostname VARCHAR(255),
    IN p_device_os VARCHAR(100),
    IN p_device_os_version VARCHAR(100),
    IN p_client_type VARCHAR(50),
    IN p_client_version VARCHAR(50),
    IN p_enrolled_ip VARCHAR(45),
    OUT p_ou_id INT,
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_secret_id INT;
    DECLARE v_ou_id INT;
    DECLARE v_is_active BOOLEAN;
    DECLARE v_existing_ou_id INT;

    -- Find the secret
    SELECT id, ou_id, is_active
    INTO v_secret_id, v_ou_id, v_is_active
    FROM ou_enrollment_secrets
    WHERE secret = p_secret
    LIMIT 1;

    -- Validate secret
    IF v_secret_id IS NULL THEN
        SET p_success = FALSE;
        SET p_message = 'Invalid enrollment secret';
        SET p_ou_id = NULL;
    ELSEIF v_is_active = FALSE THEN
        SET p_success = FALSE;
        SET p_message = 'Enrollment secret is inactive';
        SET p_ou_id = NULL;
    ELSE
        -- Check if device is already enrolled (FleetDM: enrollment is permanent)
        SELECT ou_id INTO v_existing_ou_id
        FROM device_enrollments
        WHERE device_serial = p_device_serial
        LIMIT 1;

        IF v_existing_ou_id IS NOT NULL THEN
            -- Device already enrolled, just update metadata
            UPDATE device_enrollments
            SET device_hostname = p_device_hostname,
                device_os = p_device_os,
                device_os_version = p_device_os_version,
                client_version = p_client_version,
                last_seen = NOW(),
                is_active = TRUE
            WHERE device_serial = p_device_serial;

            SET p_success = TRUE;
            SET p_message = 'Device already enrolled, metadata updated';
            SET p_ou_id = v_existing_ou_id;
        ELSE
            -- New enrollment
            INSERT INTO device_enrollments (
                ou_id, enrollment_secret_id, device_serial, device_hostname,
                device_os, device_os_version, client_type, client_version,
                enrolled_ip, last_seen, is_active
            ) VALUES (
                v_ou_id, v_secret_id, p_device_serial, p_device_hostname,
                p_device_os, p_device_os_version, p_client_type, p_client_version,
                p_enrolled_ip, NOW(), TRUE
            );

            SET p_success = TRUE;
            SET p_message = 'Device enrolled successfully';
            SET p_ou_id = v_ou_id;
        END IF;
    END IF;
END$$
DELIMITER ;

-- Procedure: Update device last seen timestamp
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS sp_update_device_last_seen(
    IN p_device_serial VARCHAR(255)
)
BEGIN
    UPDATE device_enrollments
    SET last_seen = NOW()
    WHERE device_serial = p_device_serial;
END$$
DELIMITER ;
