CREATE DATABASE IF NOT EXISTS uni_scholar_works;
USE uni_scholar_works;

-- Students
CREATE TABLE students (
    student_id VARCHAR(50) PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL
);

-- Teachers
CREATE TABLE teachers (
    teacher_id VARCHAR(50) PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL
);

-- Reports
CREATE TABLE reports (
    report_id       INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    summary         TEXT,
    type            VARCHAR(50),
    supervisor      VARCHAR(50),
    link            VARCHAR(500),
    file_id         VARCHAR(100),
    submitter_id    VARCHAR(50),
    submission_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supervisor)   REFERENCES teachers(teacher_id),
    FOREIGN KEY (submitter_id) REFERENCES students(student_id)
);

-- Reviews
CREATE TABLE reviews (
    review_id   INT AUTO_INCREMENT PRIMARY KEY,
    report_id   INT NOT NULL,
    teacher_id  VARCHAR(50),
    decision    VARCHAR(20),
    comment     TEXT,
    pdf_allowed TINYINT(1) DEFAULT 0,
    review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id)  REFERENCES reports(report_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

-- Report Authors (one report can have multiple authors)
CREATE TABLE report_authors (
    report_id  INT NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (report_id, student_id),
    FOREIGN KEY (report_id)  REFERENCES reports(report_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Report Tags
CREATE TABLE report_tag (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    report_id INT NOT NULL,
    tag       VARCHAR(100),
    FOREIGN KEY (report_id) REFERENCES reports(report_id)
);