-- =====================================================================
-- SMART WOMEN SAFETY ALERT SYSTEM - DATABASE SCHEMA (MySQL 8+)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `smart_safety_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `smart_safety_db`;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `phone` VARCHAR(25) NOT NULL UNIQUE,
    `hashed_password` VARCHAR(255) NOT NULL,
    `role` ENUM('user', 'helper', 'admin') DEFAULT 'user',
    `is_verified_helper` BOOLEAN DEFAULT FALSE,
    `address` VARCHAR(255) NULL,
    `emergency_notes` TEXT NULL,
    `battery_level` INT DEFAULT 100,
    `network_status` VARCHAR(50) DEFAULT 'Online',
    `last_latitude` DECIMAL(10, 8) NULL,
    `last_longitude` DECIMAL(11, 8) NULL,
    `last_location_time` DATETIME NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Emergency Contacts & Family/Friends Network Table
CREATE TABLE IF NOT EXISTS `emergency_contacts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `contact_name` VARCHAR(120) NOT NULL,
    `relationship` VARCHAR(50) NOT NULL, -- 'Family', 'Friend', 'Neighbour', 'Guardian'
    `phone_number` VARCHAR(25) NOT NULL,
    `email` VARCHAR(150) NULL,
    `is_priority` BOOLEAN DEFAULT TRUE,
    `invitation_status` ENUM('pending', 'accepted', 'rejected') DEFAULT 'accepted',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 3. Community Helpers / Neighbourhood Network
CREATE TABLE IF NOT EXISTS `community_helpers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `neighbourhood` VARCHAR(150) NOT NULL,
    `city` VARCHAR(100) NOT NULL,
    `police_station_jurisdiction` VARCHAR(150) NULL,
    `verification_document` VARCHAR(255) NULL,
    `verification_status` ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    `is_available` BOOLEAN DEFAULT TRUE,
    `latitude` DECIMAL(10, 8) NULL,
    `longitude` DECIMAL(11, 8) NULL,
    `accepted_requests_count` INT DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 4. Emergency SOS Alerts
CREATE TABLE IF NOT EXISTS `emergency_alerts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `trigger_type` ENUM('button', 'shake', 'voice', 'route_deviation', 'timer_checkin') DEFAULT 'button',
    `alert_mode` ENUM('normal', 'silent') DEFAULT 'normal',
    `status` ENUM('active', 'acknowledged', 'resolved', 'cancelled') DEFAULT 'active',
    `latitude` DECIMAL(10, 8) NOT NULL,
    `longitude` DECIMAL(11, 8) NOT NULL,
    `location_address` VARCHAR(255) NULL,
    `audio_recording_url` VARCHAR(255) NULL,
    `battery_level_at_alert` INT DEFAULT 100,
    `network_status_at_alert` VARCHAR(50) DEFAULT 'Online',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `resolved_at` DATETIME NULL,
    `notes` TEXT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 5. Emergency Alert Acknowledgements
CREATE TABLE IF NOT EXISTS `alert_acknowledgements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `alert_id` INT NOT NULL,
    `responder_id` INT NOT NULL,
    `responder_role` VARCHAR(50) NOT NULL, -- 'contact', 'community_helper', 'admin'
    `responder_name` VARCHAR(120) NOT NULL,
    `responder_phone` VARCHAR(25) NOT NULL,
    `eta_minutes` INT DEFAULT 10,
    `message` VARCHAR(255) NULL,
    `acknowledged_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`alert_id`) REFERENCES `emergency_alerts`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`responder_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 6. GPS Location History
CREATE TABLE IF NOT EXISTS `location_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `latitude` DECIMAL(10, 8) NOT NULL,
    `longitude` DECIMAL(11, 8) NOT NULL,
    `speed` FLOAT DEFAULT 0.0,
    `accuracy` FLOAT DEFAULT 10.0,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 7. Safe Zones & Geofencing (Home, College, Workplace)
CREATE TABLE IF NOT EXISTS `safe_zones` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `zone_name` VARCHAR(100) NOT NULL, -- 'Home', 'College', 'Workplace'
    `latitude` DECIMAL(10, 8) NOT NULL,
    `longitude` DECIMAL(11, 8) NOT NULL,
    `radius_meters` INT DEFAULT 300,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 8. Journeys & Active Tracking
CREATE TABLE IF NOT EXISTS `journeys` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `origin_name` VARCHAR(200) NOT NULL,
    `origin_lat` DECIMAL(10, 8) NOT NULL,
    `origin_lng` DECIMAL(11, 8) NOT NULL,
    `destination_name` VARCHAR(200) NOT NULL,
    `destination_lat` DECIMAL(10, 8) NOT NULL,
    `destination_lng` DECIMAL(11, 8) NOT NULL,
    `status` ENUM('in_progress', 'completed', 'deviated', 'cancelled') DEFAULT 'in_progress',
    `risk_level` ENUM('SAFE', 'WARNING', 'HIGH RISK') DEFAULT 'SAFE',
    `expected_arrival_time` DATETIME NULL,
    `start_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `end_time` DATETIME NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 9. Crime Hotspots & Community Reported Incidents
CREATE TABLE IF NOT EXISTS `incident_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `reporter_id` INT NULL,
    `incident_type` VARCHAR(100) NOT NULL, -- 'Harassment', 'Poor Lighting', 'Isolated Area', 'Suspicious Activity'
    `description` TEXT NOT NULL,
    `risk_level` ENUM('SAFE', 'WARNING', 'HIGH RISK') DEFAULT 'WARNING',
    `latitude` DECIMAL(10, 8) NOT NULL,
    `longitude` DECIMAL(11, 8) NOT NULL,
    `reported_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_verified` BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (`reporter_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
);

-- 10. Safety Check-Ins
CREATE TABLE IF NOT EXISTS `safety_checkins` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `duration_minutes` INT NOT NULL,
    `status` ENUM('pending', 'completed', 'missed_alert_triggered') DEFAULT 'pending',
    `checkin_deadline` DATETIME NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);
