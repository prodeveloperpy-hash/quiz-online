CREATE DATABASE IF NOT EXISTS online_quiz CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'quiz_user'@'localhost' IDENTIFIED BY 'quiz_password';
GRANT ALL PRIVILEGES ON online_quiz.* TO 'quiz_user'@'localhost';
FLUSH PRIVILEGES;

