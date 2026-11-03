
CREATE DATABASE IF NOT EXISTS campus_complaints_new;

USE campus_complaints_new;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'faculty') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. COMPLAINTS TABLE
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,

    category ENUM(
        'Infrastructure',
        'Electrical',
        'Internet',
        'Cleanliness',
        'Water',
        'Other'
    ) NOT NULL,

    description TEXT NOT NULL,

    priority ENUM(
        'Low',
        'Medium',
        'High',
        'Urgent'
    ) DEFAULT 'Medium',

    assigned_to VARCHAR(100) NULL,

    status ENUM(
        'Submitted',
        'Assigned',
        'In Progress',
        'Resolved',
        'Rejected'
    ) DEFAULT 'Submitted',

    resolution TEXT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
    REFERENCES users(user_id)
);

-- 3. COMPLAINT HISTORY TABLE
CREATE TABLE IF NOT EXISTS complaint_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    changed_by INT NULL,
    old_status VARCHAR(30) NULL,
    new_status VARCHAR(30) NOT NULL,
    remarks TEXT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (complaint_id)
    REFERENCES complaints(complaint_id),

    FOREIGN KEY (changed_by)
    REFERENCES users(user_id)
    ON DELETE SET NULL
);

-- 4. CREATE FACULTY ACCOUNT
INSERT INTO users (
    name,
    email,
    password_hash,
    role
)
VALUES (
    'Faculty Admin',
    'faculty@gmail.com',
    'scrypt:32768:8:1$US3mLeDxsWj5ntRV$7fd2c8d5e33926151eb38f2611f74b5a736475d42f60ca2b9578e9b230e6899baa28c4114d50bfe6cafec21a17ae11c120bf6fced70e6afd0c939ed0d236a22f',
    'faculty'
)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role = 'faculty';

-- 5. VERIFY TABLES
SHOW TABLES;

-- 6. VIEW USERS
SELECT * FROM users;

-- 7. VIEW COMPLAINTS
SELECT * FROM complaints;

-- 8. VIEW COMPLAINT HISTORY
SELECT * FROM complaint_history;

-- 9. VERIFY FACULTY ACCOUNT
SELECT user_id, name, email, role
FROM users
WHERE email = 'faculty@gmail.com';
