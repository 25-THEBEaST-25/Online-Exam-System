-- ════════════════════════════════════════════════════════════
-- ExamCloud  ·  MySQL Setup Script
-- Run this once before starting the Flask app
-- ════════════════════════════════════════════════════════════

-- 1. Create database
CREATE DATABASE IF NOT EXISTS online_exam_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE online_exam_db;

-- 2. Users table (admin + students)
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(100)  NOT NULL UNIQUE,
    password    VARCHAR(255)  NOT NULL,          -- SHA-256 hex
    role        ENUM('admin','student') NOT NULL DEFAULT 'student',
    email       VARCHAR(150),
    full_name   VARCHAR(150)
);

-- 3. Exams table
CREATE TABLE IF NOT EXISTS exams (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    exam_name   VARCHAR(200) NOT NULL,
    duration    INT          NOT NULL DEFAULT 10,  -- minutes
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    is_active   TINYINT(1)   DEFAULT 1
);

-- 4. Questions table (MCQ only)
CREATE TABLE IF NOT EXISTS questions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    exam_id        INT  NOT NULL,
    question       TEXT NOT NULL,
    option1        VARCHAR(300) NOT NULL,
    option2        VARCHAR(300) NOT NULL,
    option3        VARCHAR(300) NOT NULL,
    option4        VARCHAR(300) NOT NULL,
    correct_answer TINYINT NOT NULL,  -- 1=A, 2=B, 3=C, 4=D
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

-- 5. Results table
CREATE TABLE IF NOT EXISTS results (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT NOT NULL,
    exam_id      INT NOT NULL,
    score        INT NOT NULL DEFAULT 0,
    total        INT NOT NULL DEFAULT 0,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (exam_id)    REFERENCES exams(id)
);

-- 6. Default admin account
--    Username: admin  |  Password: admin123
INSERT IGNORE INTO users (username, password, role, full_name)
VALUES (
  'admin',
  '240be518fabd2724ddb6f04eeb1da5967448d7e831d9a0c4df5c18bc3c2e8e81',  -- SHA-256 of "admin123"
  'admin',
  'Administrator'
);

-- ─── Sample data (optional — comment out if not needed) ──────

INSERT IGNORE INTO exams (id, exam_name, duration) VALUES
  (1, 'Python Basics — Demo Exam', 15);

INSERT IGNORE INTO questions
  (exam_id, question, option1, option2, option3, option4, correct_answer)
VALUES
  (1, 'Which keyword is used to define a function in Python?',
   'func', 'define', 'def', 'function', 3),
  (1, 'What is the output of print(2 ** 3)?',
   '5', '6', '8', '9', 3),
  (1, 'Which data type is immutable in Python?',
   'list', 'dict', 'set', 'tuple', 4),
  (1, 'What does len([1,2,3]) return?',
   '1', '2', '3', '4', 3),
  (1, 'Which of the following is NOT a valid Python loop?',
   'for', 'while', 'do-while', 'for-in', 3);

SELECT 'Setup complete! Default admin: admin / admin123' AS status;
