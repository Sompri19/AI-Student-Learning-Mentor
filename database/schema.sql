-- =====================================================================
-- Database Schema: student_learning_mentor
-- Project: AI Student Learning Mentor (Phase 1)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `student_learning_mentor`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `student_learning_mentor`;

-- ---------------------------------------------------------------------
-- 1. Table: users
-- Core authentication and user management table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(191) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'student',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. Table: student_profiles
-- Academic profile and learning preferences for students
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `student_profiles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `education_level` VARCHAR(50) NULL,
    `course` VARCHAR(100) NULL,
    `semester` VARCHAR(20) NULL,
    `skill_level` VARCHAR(30) NULL,
    `learning_goal` TEXT NULL,
    `preferred_study_time` VARCHAR(50) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_student_profiles_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. Table: subjects
-- Academic subjects/courses available in the curriculum
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `subjects` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. Table: topics
-- Specific syllabus topics under each subject
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `topics` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `subject_id` INT NOT NULL,
    `topic_name` VARCHAR(150) NOT NULL,
    `description` TEXT NULL,
    `difficulty` VARCHAR(30) NOT NULL DEFAULT 'Beginner',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_topics_subject` (`subject_id`),
    CONSTRAINT `fk_topics_subject`
        FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. Table: resources
-- Verified educational resources associated with specific topics
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `resources` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `topic_id` INT NOT NULL,
    `title` VARCHAR(200) NOT NULL,
    `resource_type` VARCHAR(50) NOT NULL,
    `url` VARCHAR(500) NOT NULL,
    `description` TEXT NULL,
    `difficulty` VARCHAR(30) NOT NULL DEFAULT 'Beginner',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_resources_topic` (`topic_id`),
    CONSTRAINT `fk_resources_topic`
        FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. Table: study_plans
-- High-level study plan generated for a student
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_plans` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `subject_id` INT NOT NULL,
    `goal` TEXT NOT NULL,
    `duration_days` INT NOT NULL DEFAULT 7,
    `skill_level` VARCHAR(30) NOT NULL DEFAULT 'Beginner',
    `preferred_study_time` VARCHAR(50) NOT NULL DEFAULT 'Flexible',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_study_plans_user` (`user_id`),
    INDEX `idx_study_plans_subject` (`subject_id`),
    CONSTRAINT `fk_study_plans_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_study_plans_subject`
        FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 7. Table: study_plan_items
-- Day-by-day learning tasks within a study plan
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_plan_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `study_plan_id` INT NOT NULL,
    `day_number` INT NOT NULL,
    `topic_id` INT NOT NULL,
    `task` TEXT NOT NULL,
    `completed` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_plan_items_plan` (`study_plan_id`),
    INDEX `idx_plan_items_topic` (`topic_id`),
    CONSTRAINT `fk_plan_items_plan`
        FOREIGN KEY (`study_plan_id`) REFERENCES `study_plans` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_plan_items_topic`
        FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 8. Table: quizzes
-- Topic-based practice questions
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `quizzes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `topic_id` INT NOT NULL,
    `question` TEXT NOT NULL,
    `option_a` VARCHAR(255) NOT NULL,
    `option_b` VARCHAR(255) NOT NULL,
    `option_c` VARCHAR(255) NOT NULL,
    `option_d` VARCHAR(255) NOT NULL,
    `correct_answer` VARCHAR(10) NOT NULL,
    `difficulty` VARCHAR(30) NOT NULL DEFAULT 'Medium',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_quizzes_topic` (`topic_id`),
    CONSTRAINT `fk_quizzes_topic`
        FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 9. Table: quiz_attempts
-- Records of student multi-question practice attempts and scores
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `quiz_attempts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `topic_id` INT NOT NULL,
    `total_questions` INT NOT NULL DEFAULT 1,
    `correct_answers` INT NOT NULL DEFAULT 0,
    `score_percentage` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    `quiz_id` INT NULL,
    `selected_answer` VARCHAR(10) NULL,
    `is_correct` BOOLEAN NULL DEFAULT FALSE,
    `score` DECIMAL(5, 2) NULL DEFAULT 0.00,
    `attempted_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_quiz_attempts_user` (`user_id`),
    INDEX `idx_quiz_attempts_topic` (`topic_id`),
    CONSTRAINT `fk_quiz_attempts_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_quiz_attempts_topic`
        FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    -- Optional single-question reference retained from the legacy attempt format
    CONSTRAINT `fk_quiz_attempts_quiz`
        FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 9b. Table: quiz_attempt_answers
-- Individual question responses within a student quiz attempt
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `quiz_attempt_answers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `attempt_id` INT NOT NULL,
    `quiz_id` INT NOT NULL,
    `selected_answer` VARCHAR(10) NOT NULL,
    `correct_answer` VARCHAR(10) NOT NULL,
    `is_correct` BOOLEAN NOT NULL DEFAULT FALSE,
    INDEX `idx_attempt_answers_attempt` (`attempt_id`),
    INDEX `idx_attempt_answers_quiz` (`quiz_id`),
    CONSTRAINT `fk_attempt_answers_attempt`
        FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_attempt_answers_quiz`
        FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 10. Table: progress
-- Student mastery and completion percentage per topic
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `progress` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `topic_id` INT NOT NULL,
    `completion_percentage` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_user_topic` (`user_id`, `topic_id`),
    INDEX `idx_progress_user` (`user_id`),
    INDEX `idx_progress_topic` (`topic_id`),
    CONSTRAINT `fk_progress_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_progress_topic`
        FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 11. Table: ai_chats
-- Academic query logs between students and the AI mentor
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `ai_chats` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `question` TEXT NOT NULL,
    `answer` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_ai_chats_user` (`user_id`),
    CONSTRAINT `fk_ai_chats_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- DOCUMENTED STATIC SEED DATA
-- Purpose: Real educational subjects and foundational topics to verify
-- the database architecture during initial setup.
-- Note: NO fake users, NO fake student profiles, NO fake progress, and
-- NO fake quiz attempts are inserted.
-- =====================================================================

INSERT IGNORE INTO `subjects` (`id`, `name`, `description`) VALUES
(1, 'Python Programming', 'Fundamental and advanced concepts of Python programming language including syntax, data structures, and modular design.'),
(2, 'Data Structures & Algorithms', 'Core data structures, algorithm analysis, recursion, sorting, searching, and algorithmic problem-solving paradigms.'),
(3, 'Web Development Basics', 'Foundations of modern frontend development: HTML5 semantic markup, CSS3 styling, responsive layouts, and JavaScript fundamentals.'),
(4, 'Java Programming', 'Object-oriented programming using Java: strong typing, classes, inheritance, polymorphism, exception handling, and collections.'),
(5, 'Database Management Systems', 'Relational database concepts, ER modeling, SQL querying, schema normalization, ACID transactions, and index optimization.'),
(6, 'Computer Networks', 'Principles of computer communications: OSI and TCP/IP protocol stacks, IP addressing, routing, transport layer protocols, and sockets.'),
(7, 'Operating Systems', 'Internal architecture of operating systems: process scheduling, inter-process communication, multithreading, and memory paging.');

INSERT IGNORE INTO `topics` (`id`, `subject_id`, `topic_name`, `description`, `difficulty`) VALUES
(1, 1, 'Variables & Data Types', 'Numbers, strings, booleans, lists, dictionaries, tuples, and type casting in Python.', 'Beginner'),
(2, 1, 'Control Structures', 'Conditional branching with if-elif-else, while loops, and for loops with range.', 'Beginner'),
(3, 1, 'Functions & Modules', 'Defining functions, positional/keyword arguments, return values, scope, and importing standard libraries.', 'Intermediate'),
(4, 2, 'Arrays & Linked Lists', 'Contiguous arrays vs node-based singly and doubly linked lists, operations and time complexities.', 'Beginner'),
(5, 2, 'Stacks & Queues', 'LIFO and FIFO data structures, stack-based expression evaluation, queue buffers, and deque.', 'Intermediate'),
(6, 3, 'Semantic HTML & Document Structure', 'HTML5 document structure, semantic tags, forms, input types, and accessibility guidelines.', 'Beginner'),
(7, 1, 'Lists, Tuples & Sets', 'Sequential collection operations, indexing, slicing, comprehensions, and set algebra in Python.', 'Beginner'),
(8, 1, 'Dictionaries & Hash Maps', 'Key-value pair mappings, dictionary methods, nested dictionaries, and frequency counting.', 'Intermediate'),
(9, 2, 'Binary Trees & BST', 'Hierarchical tree nodes, in-order/pre-order traversals, and binary search tree lookup/insertion.', 'Advanced'),
(10, 3, 'CSS Layouts & Responsive Design', 'Box model, Flexbox alignment, CSS Grid, media queries, and responsive viewport design.', 'Beginner'),
(11, 3, 'JavaScript Fundamentals', 'Variables, arrow functions, DOM manipulation, event listeners, and asynchronous fetch requests.', 'Intermediate'),
(12, 4, 'Java Syntax & Primitive Types', 'Java main method, primitive types, operators, variable declarations, and type casting.', 'Beginner'),
(13, 4, 'Classes & Object-Oriented Principles', 'Class definitions, constructors, encapsulation, getters/setters, inheritance, and method overriding.', 'Intermediate'),
(14, 4, 'Java Collections Framework', 'List, Set, Map interfaces, ArrayList, HashMap, and standard iteration patterns.', 'Intermediate'),
(15, 5, 'Database Fundamentals & ER Model', 'Relational database concepts, tables, primary/foreign keys, entity-relationship diagrams, and cardinality.', 'Beginner'),
(16, 5, 'SQL Queries & Joins', 'SELECT queries, WHERE filtering, GROUP BY aggregations, INNER/LEFT/RIGHT JOINs, and subqueries.', 'Intermediate'),
(17, 5, 'Normalization & Normal Forms', 'Data redundancy elimination, 1NF, 2NF, 3NF, BCNF, functional dependencies, and lossless joins.', 'Advanced'),
(18, 6, 'Network Fundamentals & OSI Model', 'Network topologies, layered architectures, the 7-layer OSI model, and the 4-layer TCP/IP suite.', 'Beginner'),
(19, 6, 'IP Addressing & Subnetting', 'IPv4 classless addressing, CIDR notation, subnet masks, network vs host IDs, and IPv6 overview.', 'Intermediate'),
(20, 6, 'TCP/IP & Transport Protocols', 'Reliable TCP 3-way handshake, flow control, congestion control, and connectionless UDP.', 'Intermediate'),
(21, 7, 'Processes & Process Management', 'Process control blocks (PCB), process state transitions, context switching, and fork/exec lifecycles.', 'Beginner'),
(22, 7, 'CPU Scheduling Algorithms', 'First-Come First-Served (FCFS), Shortest Job First (SJF), Round Robin (RR), and Priority Scheduling.', 'Intermediate'),
(23, 7, 'Memory Management & Virtual Memory', 'Paging, segmentation, page tables, page faults, and virtual memory swap mechanics.', 'Advanced');

INSERT IGNORE INTO `resources` (`id`, `topic_id`, `title`, `resource_type`, `url`, `description`, `difficulty`) VALUES
(1, 1, 'Python Official Documentation: Data Types', 'Documentation', 'https://docs.python.org/3/tutorial/introduction.html', 'Official Python guide covering numbers, strings, and list indexing fundamentals.', 'Beginner'),
(2, 1, 'Understanding Python Variable Scoping', 'Article', 'https://realpython.com/python-variables/', 'Comprehensive article explaining variable assignment, dynamic typing, and object references.', 'Beginner'),
(3, 1, 'Interactive Data Types Exercises', 'Practice', 'https://www.w3schools.com/python/python_datatypes.asp', 'Self-paced code challenges and syntax quizzes on Python data types.', 'Beginner'),
(4, 2, 'Python Control Flow Guide', 'Documentation', 'https://docs.python.org/3/tutorial/controlflow.html', 'Official guide on if statements, for loops, and the range() function.', 'Beginner'),
(5, 2, 'Python Loops and Branching Notes', 'Notes', 'https://realpython.com/python-conditional-statements/', 'Detailed study notes on boolean conditions and loop control keywords (break, continue).', 'Beginner'),
(6, 3, 'Defining Functions in Python', 'Documentation', 'https://docs.python.org/3/tutorial/controlflow.html#defining-functions', 'In-depth guide on defining functions, default arguments, and lambda expressions.', 'Intermediate'),
(7, 3, 'Python Modular Programming & Packages', 'Article', 'https://realpython.com/python-modules-packages/', 'Tutorial on structuring reusable Python modules and packages.', 'Intermediate'),
(8, 4, 'Linked List Fundamentals & Node Structures', 'Notes', 'https://www.geeksforgeeks.org/data-structures/linked-list/', 'Curated notes on singly, doubly, and circular linked lists with pointer tracing.', 'Beginner'),
(9, 4, 'Array Memory Layout and Big-O Complexity', 'Article', 'https://www.geeksforgeeks.org/array-data-structure/', 'Deep dive into array indexing speed, memory cache locality, and algorithmic trade-offs.', 'Beginner'),
(10, 4, 'Linked List Implementation Practice', 'Practice', 'https://leetcode.com/explore/learn/card/linked-list/', 'Interactive coding challenges focusing on linked list reversal and node insertion.', 'Intermediate'),
(11, 5, 'Stack and Queue ADT Specification', 'Documentation', 'https://www.geeksforgeeks.org/stack-data-structure/', 'Formal abstract data type definitions, LIFO/FIFO invariants, and array/list implementations.', 'Intermediate'),
(12, 5, 'Balanced Parentheses & Monotonic Stack Notes', 'Notes', 'https://cp-algorithms.com/data_structures/stack_queue_modification.html', 'Study notes on classic stack interview applications and monotonic queue patterns.', 'Intermediate'),
(13, 6, 'MDN Web Docs: HTML Basics', 'Documentation', 'https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics', 'Mozilla Developer Network foundational tutorial on HTML elements and page structuring.', 'Beginner'),
(14, 6, 'Semantic HTML Elements and Web Accessibility', 'Article', 'https://developer.mozilla.org/en-US/docs/Glossary/Semantics', 'Guide to choosing semantic elements (article, section, nav) for accessibility.', 'Beginner'),
(15, 10, 'MDN Guide to CSS Flexbox', 'Documentation', 'https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Flexbox', 'Comprehensive guide to flexible box layouts, axis directions, and alignment properties.', 'Beginner'),
(16, 10, 'A Complete Guide to CSS Grid', 'Article', 'https://css-tricks.com/snippets/css/complete-guide-grid/', 'Visual reference for grid container properties and track alignments.', 'Intermediate'),
(17, 13, 'Oracle Java Tutorials: Object-Oriented Programming', 'Documentation', 'https://docs.oracle.com/javase/tutorial/java/concepts/', 'Official Oracle tutorials explaining classes, objects, interfaces, and inheritance.', 'Intermediate'),
(18, 13, 'Java OOP Best Practices & Encapsulation', 'Article', 'https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/', 'Practical guide on constructors, access modifiers, and SOLID design principles.', 'Intermediate'),
(19, 16, 'PostgreSQL / MySQL SELECT and JOIN Reference', 'Documentation', 'https://dev.mysql.com/doc/refman/8.0/en/select.html', 'Official SQL syntax reference for joins, aggregations, and grouping clauses.', 'Intermediate'),
(20, 16, 'Visual Explanation of SQL Joins', 'Notes', 'https://blog.codinghorror.com/a-visual-explanation-of-sql-joins/', 'Intuitive Venn diagrams and record matching examples for inner, outer, and cross joins.', 'Beginner'),
(21, 16, 'Interactive SQL Practice Sandbox', 'Practice', 'https://sqlzoo.net/', 'Hands-on browser-based SQL exercises with real table schemas and automated feedback.', 'Intermediate'),
(22, 18, 'Cloudflare Learning: The OSI 7-Layer Model', 'Article', 'https://www.cloudflare.com/learning/ddos/glossary/open-systems-interconnection-model-osi/', 'Clear breakdown of physical, data link, network, transport, session, presentation, and application layers.', 'Beginner'),
(23, 18, 'TCP/IP Protocol Suite Study Notes', 'Notes', 'https://www.geeksforgeeks.org/tcp-ip-model/', 'Comparison table between OSI 7 layers and the 4 TCP/IP layers with protocol examples.', 'Beginner'),
(24, 22, 'OSTEP: CPU Scheduling Principles', 'Notes', 'https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf', 'Free textbook chapter from Operating Systems: Three Easy Pieces on scheduling policies.', 'Intermediate'),
(25, 22, 'Comparative Analysis of SJF, Round Robin, and Multi-Level Queue', 'Article', 'https://www.geeksforgeeks.org/cpu-scheduling-in-operating-systems/', 'Detailed breakdown of turnaround time, waiting time, and preemptive context overhead.', 'Intermediate');
