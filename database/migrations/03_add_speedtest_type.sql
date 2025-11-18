-- Migration: Add 'speedtest' to test_type enum
-- This allows storing speedtest results alongside network tests

USE waddleperf;

-- Modify server_test_results to support speedtest
ALTER TABLE server_test_results
MODIFY COLUMN test_type ENUM('http', 'tcp', 'udp', 'icmp', 'speedtest') NOT NULL;

-- Modify client_test_results to support speedtest
ALTER TABLE client_test_results
MODIFY COLUMN test_type ENUM('http', 'tcp', 'udp', 'icmp', 'speedtest') NOT NULL;

-- Add index for speedtest queries
ALTER TABLE server_test_results
ADD INDEX idx_speedtest_created (test_type, created_at)
USING BTREE;

ALTER TABLE client_test_results
ADD INDEX idx_speedtest_created (test_type, created_at)
USING BTREE;
