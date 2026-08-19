-- Run this once to set up the database.
-- mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS sign_language_db;
USE sign_language_db;

CREATE TABLE IF NOT EXISTS recognized_signs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sign_text VARCHAR(100) NOT NULL,
    confidence FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: a small vocabulary reference table, useful if you want to
-- expand the gesture_classifier.py lookup table later and keep the
-- meanings documented in the database too.
CREATE TABLE IF NOT EXISTS sign_vocabulary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sign_text VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

INSERT INTO sign_vocabulary (sign_text, description) VALUES
    ('Hello', 'Open palm, all five fingers extended'),
    ('No', 'Closed fist, no fingers extended'),
    ('Yes', 'Thumb extended, other fingers folded'),
    ('I Love You', 'Thumb, index, and pinky extended'),
    ('Peace', 'Index and middle fingers extended'),
    ('One', 'Index finger extended only'),
    ('Stop', 'Index, middle, ring, and pinky extended, thumb folded'),
    ('OK', 'Thumb, index, and middle fingers extended')
ON DUPLICATE KEY UPDATE description = VALUES(description);
