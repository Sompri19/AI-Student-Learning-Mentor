-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: 172.17.160.1    Database: edumentor_ai
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ai_chats`
--

DROP TABLE IF EXISTS `ai_chats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ai_chats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `question` text NOT NULL,
  `answer` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_ai_chats_user` (`user_id`),
  CONSTRAINT `fk_ai_chats_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=278 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_chats`
--

LOCK TABLES `ai_chats` WRITE;
/*!40000 ALTER TABLE `ai_chats` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_chats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `progress`
--

DROP TABLE IF EXISTS `progress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `progress` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `topic_id` int(11) NOT NULL,
  `completion_percentage` decimal(5,2) NOT NULL DEFAULT 0.00,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_topic` (`user_id`,`topic_id`),
  KEY `idx_progress_user` (`user_id`),
  KEY `idx_progress_topic` (`topic_id`),
  CONSTRAINT `fk_progress_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_progress_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=648 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `progress`
--

LOCK TABLES `progress` WRITE;
/*!40000 ALTER TABLE `progress` DISABLE KEYS */;
INSERT INTO `progress` VALUES (542,2019,12,75.00,'2026-10-12 09:33:12'),(543,2019,13,75.00,'2026-10-12 09:33:10'),(544,2019,14,75.00,'2026-10-12 09:33:11');
/*!40000 ALTER TABLE `progress` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quiz_attempt_answers`
--

DROP TABLE IF EXISTS `quiz_attempt_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `quiz_attempt_answers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `attempt_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `selected_answer` varchar(10) NOT NULL,
  `correct_answer` varchar(10) NOT NULL,
  `is_correct` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_attempt_answers_attempt` (`attempt_id`),
  KEY `idx_attempt_answers_quiz` (`quiz_id`),
  CONSTRAINT `fk_attempt_answers_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_attempt_answers_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1432 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quiz_attempt_answers`
--

LOCK TABLES `quiz_attempt_answers` WRITE;
/*!40000 ALTER TABLE `quiz_attempt_answers` DISABLE KEYS */;
/*!40000 ALTER TABLE `quiz_attempt_answers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quiz_attempts`
--

DROP TABLE IF EXISTS `quiz_attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `quiz_attempts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `quiz_id` int(11) DEFAULT NULL,
  `selected_answer` varchar(10) NOT NULL,
  `is_correct` tinyint(1) NOT NULL DEFAULT 0,
  `score` decimal(5,2) NOT NULL DEFAULT 0.00,
  `attempted_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `topic_id` int(11) DEFAULT NULL,
  `total_questions` int(11) NOT NULL DEFAULT 1,
  `correct_answers` int(11) NOT NULL DEFAULT 0,
  `score_percentage` decimal(5,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `idx_quiz_attempts_user` (`user_id`),
  KEY `idx_quiz_attempts_quiz` (`quiz_id`),
  CONSTRAINT `fk_quiz_attempts_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_quiz_attempts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=537 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quiz_attempts`
--

LOCK TABLES `quiz_attempts` WRITE;
/*!40000 ALTER TABLE `quiz_attempts` DISABLE KEYS */;
/*!40000 ALTER TABLE `quiz_attempts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quizzes`
--

DROP TABLE IF EXISTS `quizzes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `quizzes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topic_id` int(11) NOT NULL,
  `question` text NOT NULL,
  `option_a` varchar(255) NOT NULL,
  `option_b` varchar(255) NOT NULL,
  `option_c` varchar(255) NOT NULL,
  `option_d` varchar(255) NOT NULL,
  `correct_answer` varchar(10) NOT NULL,
  `difficulty` varchar(30) NOT NULL DEFAULT 'Medium',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_quizzes_topic` (`topic_id`),
  CONSTRAINT `fk_quizzes_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quizzes`
--

LOCK TABLES `quizzes` WRITE;
/*!40000 ALTER TABLE `quizzes` DISABLE KEYS */;
INSERT INTO `quizzes` VALUES (1,1,'Which of the following data types in Python is immutable?','list','dict','tuple','set','C','Beginner','2026-10-06 19:01:32'),(2,1,'What is the output of type(4 / 2) in Python 3?','<class \'int\'>','<class \'float\'>','<class \'double\'>','<class \'number\'>','B','Beginner','2026-10-06 19:01:32'),(3,1,'Which built-in function returns the unique identity memory address of an object in Python?','id()','mem()','ref()','loc()','A','Beginner','2026-10-06 19:01:32'),(4,1,'What happens when you execute: bool(\'False\') in Python?','Returns False','Returns True','Raises ValueError','Returns None','B','Beginner','2026-10-06 19:01:32'),(5,1,'How is dynamic typing characterized in Python?','Variables must declare a type before assignment','Variable types are determined and bound at runtime','Variable types can never change once assigned','Types are only checked during static compilation','B','Beginner','2026-10-06 19:01:32'),(6,2,'What values does range(2, 8, 2) generate in a Python for loop?','[2, 4, 6, 8]','[2, 4, 6]','[2, 3, 4, 5, 6, 7]','[4, 6, 8]','B','Beginner','2026-10-06 19:01:32'),(7,2,'Which keyword immediately terminates the innermost enclosing loop in Python?','continue','pass','break','exit','C','Beginner','2026-10-06 19:01:32'),(8,2,'What is the role of the \'pass\' statement in Python?','Skips the remainder of the current loop iteration','Acts as a syntactically required null statement / placeholder','Passes control to the parent function scope','Terminates execution of the current function','B','Beginner','2026-10-06 19:01:32'),(9,2,'When does the \'else\' block attached to a while loop execute in Python?','Only when the loop condition evaluates to False without a break','After every single iteration of the loop','Whenever a break statement terminates the loop','Only if an exception is raised inside the loop body','A','Intermediate','2026-10-06 19:01:32'),(10,2,'What is the output of: [x for x in range(5) if x % 2 == 0]?','[1, 3, 5]','[0, 2, 4]','[2, 4]','[0, 1, 2, 3, 4]','B','Beginner','2026-10-06 19:01:32'),(11,3,'What does *args syntax in a Python function definition allow?','Passing a variable number of keyword arguments as a dict','Passing a variable number of non-keyword positional arguments as a tuple','Enforcing strict type checking on positional parameters','Passing arguments by reference instead of value','B','Intermediate','2026-10-06 19:01:32'),(12,3,'If a Python function finishes execution without an explicit return statement, what does it return?','0','False','None','Undefined','C','Beginner','2026-10-06 19:01:32'),(13,3,'What is a lambda function in Python?','A recursive function with caching','A small anonymous inline function defined with the lambda keyword','A built-in module for multithreading','A function that returns multiple generator objects','B','Intermediate','2026-10-06 19:01:32'),(14,3,'What happens when mutable default arguments like def fn(lst=[]) are used across multiple calls?','A new list is created on every call','The same list instance is shared across calls and retains modifications','Python raises a SyntaxError at compile time','The list is cleared automatically upon function exit','B','Intermediate','2026-10-06 19:01:32'),(15,3,'What is the purpose of the \'__name__ == \"__main__\"\' guard in Python modules?','Ensures the module runs with administrator privileges','Allows code to execute only when run directly as a script, not when imported','Initializes the global package namespace','Optimizes module bytecode compilation speed','B','Intermediate','2026-10-06 19:01:32'),(16,7,'What is the average time complexity of membership testing (x in s) for a Python set?','O(n)','O(log n)','O(1)','O(n^2)','C','Intermediate','2026-10-06 19:01:32'),(17,7,'What is the difference between list.append(item) and list.extend(iterable)?','append adds elements individually; extend creates a new list','append adds the object as a single element; extend iterates and adds each item','extend modifies in place; append returns a copy','There is no difference in behavior','B','Beginner','2026-10-06 19:01:32'),(18,7,'What does my_list[::-1] evaluate to in Python?','An empty list','A reversed copy of the original list','The last element of the list only','Raises an IndexError','B','Beginner','2026-10-06 19:01:32'),(19,7,'Which mathematical set operation does the pipe \'|\' operator perform on Python sets?','Intersection','Union','Difference','Symmetric Difference','B','Beginner','2026-10-06 19:01:32'),(20,7,'Can a list be used as an element inside a standard Python set?','Yes, always','No, because lists are unhashable mutable objects','Yes, provided the list is sorted','Only if the list contains integers','B','Intermediate','2026-10-06 19:01:32'),(21,8,'What does my_dict.get(\'key\', \'default\') do if \'key\' is not in my_dict?','Raises a KeyError exception','Returns \'default\' without raising an error','Inserts \'key\': \'default\' into my_dict and returns \'default\'','Returns None and prints a warning','B','Beginner','2026-10-06 19:01:32'),(22,8,'What method returns a view of all (key, value) pairs as tuples in a Python dict?','my_dict.pairs()','my_dict.entries()','my_dict.items()','my_dict.tuples()','C','Beginner','2026-10-06 19:01:32'),(23,8,'What is the requirement for an object to be used as a key in a Python dictionary?','It must be iterable','It must be hashable and immutable','It must be an alphanumeric string','It must inherit from the Key base class','B','Intermediate','2026-10-06 19:01:32'),(24,8,'What is the expected average time complexity of key lookup in a Python dictionary?','O(1)','O(log n)','O(n)','O(n log n)','A','Intermediate','2026-10-06 19:01:32'),(25,8,'What happens when you iterate over a dictionary using: for x in my_dict: ?','x iterates over the dictionary values','x iterates over the dictionary keys','x iterates over (key, value) tuples','x iterates over item memory addresses','B','Beginner','2026-10-06 19:01:32'),(26,4,'Why does an array support O(1) random element access by index?','Elements are linked via contiguous heap pointers','Elements are stored in contiguous memory with computed offsets','Arrays maintain an internal binary search tree','Memory is dynamically mapped via hash tables','B','Beginner','2026-10-06 19:01:32'),(27,4,'What is the time complexity of inserting a node at the head of a singly linked list?','O(1)','O(log n)','O(n)','O(n^2)','A','Beginner','2026-10-06 19:01:32'),(28,4,'What additional pointer does each node in a doubly linked list contain compared to a singly linked list?','Child pointer','Previous pointer','Parent pointer','Hash pointer','B','Beginner','2026-10-06 19:01:32'),(29,4,'What is the main drawback of standard linked lists compared to arrays regarding CPU cache performance?','Linked list nodes require more sorting passes','Linked list nodes are scattered across memory, causing poor cache locality','Linked lists cannot store dynamic data types','Linked list pointers cause continuous stack overflows','B','Intermediate','2026-10-06 19:01:32'),(30,4,'What is the time complexity to find the middle node of a singly linked list using the slow-fast pointer technique?','O(1)','O(n)','O(n log n)','O(n^2)','B','Intermediate','2026-10-06 19:01:32'),(31,5,'Which operational principle defines the behavior of a Stack?','First-In, First-Out (FIFO)','Last-In, First-Out (LIFO)','Priority-Based Extraction','Random Access Extraction','B','Beginner','2026-10-06 19:01:32'),(32,5,'Which standard data structure is utilized by the CPU runtime to manage nested function calls and return addresses?','Queue','Stack','Priority Queue','Circular Array','B','Beginner','2026-10-06 19:01:32'),(33,5,'Which classic problem is most effectively solved using a Stack?','Breadth-First Search (BFS) of a graph','Valid Parentheses Matching in syntax analysis','Round Robin CPU Scheduling','Dijkstra\'s Shortest Path Algorithm','B','Intermediate','2026-10-06 19:01:32'),(34,5,'In a standard Queue, at which end do element insertions (enqueue) take place?','Front','Rear','Top','Center','B','Beginner','2026-10-06 19:01:32'),(35,5,'What is a Deque (Double-Ended Queue)?','A queue that only accepts double precision numbers','A sequence where insertions and deletions are permitted at both ends','A queue implemented with two separate relational databases','A stack that reverses order every two operations','B','Intermediate','2026-10-06 19:01:32'),(36,9,'What property defines a valid Binary Search Tree (BST)?','Every node must have exactly two child nodes','Left subtree values < root value < right subtree values for every node','The tree must always be completely full at the bottom level','Nodes at odd depths must contain even numbers','B','Intermediate','2026-10-06 19:01:32'),(37,9,'Which traversal of a Binary Search Tree produces node values in strictly sorted ascending order?','Pre-order Traversal','In-order Traversal','Post-order Traversal','Level-order Traversal','B','Intermediate','2026-10-06 19:01:32'),(38,9,'What is the worst-case search time complexity in an unbalanced, skewed Binary Search Tree?','O(1)','O(log n)','O(n)','O(n log n)','C','Intermediate','2026-10-06 19:01:32'),(39,9,'What is a leaf node in a tree data structure?','The topmost node of the tree','A node that has no children','A node with exactly one child','A node containing a duplicate key','B','Beginner','2026-10-06 19:01:32'),(40,9,'What is the maximum number of nodes in a binary tree of height h (where height of root is 0)?','2^h','2^(h + 1) - 1','2^h - 1','h^2','B','Advanced','2026-10-06 19:01:32'),(41,6,'Which HTML5 tag is used to denote the primary central content of a web page document?','<header>','<main>','<section>','<div>','B','Beginner','2026-10-06 19:01:32'),(42,6,'Why is semantic HTML important in web engineering?','It compiles faster into machine instructions','It enhances accessibility (screen readers) and search engine indexing (SEO)','It automatically applies CSS styling without any stylesheet','It secures HTTP requests from cross-site scripting','B','Beginner','2026-10-06 19:01:32'),(43,6,'Which attribute on an <img> tag provides alternative text for accessibility when the image fails to load?','title','src','alt','aria-desc','C','Beginner','2026-10-06 19:01:32'),(44,6,'What is the purpose of the \'<meta charset=\"UTF-8\">\' tag?','Specifies the CSS framework version','Declares the character encoding used for the document','Forces HTTPS communication','Configures mobile viewport scaling','B','Beginner','2026-10-06 19:01:32'),(45,6,'Which HTML5 input type provides built-in email format validation in the browser?','<input type=\"text\">','<input type=\"mail\">','<input type=\"email\">','<input type=\"validate\">','C','Beginner','2026-10-06 19:01:32'),(46,10,'What are the 4 fundamental layers of the CSS Box Model, from innermost to outermost?','Margin -> Border -> Padding -> Content','Content -> Padding -> Border -> Margin','Border -> Margin -> Padding -> Content','Content -> Margin -> Padding -> Border','B','Beginner','2026-10-06 19:01:32'),(47,10,'Which CSS Flexbox property aligns items along the main axis?','align-items','justify-content','align-content','flex-direction','B','Beginner','2026-10-06 19:01:32'),(48,10,'What is the effect of setting \'box-sizing: border-box;\' in CSS?','Padding and border are included within the element\'s specified width and height','Margins are completely removed from all elements','Borders are hidden unless hovered','Content overflows without clipping','A','Intermediate','2026-10-06 19:01:32'),(49,10,'Which CSS at-rule is used to apply style rules conditionally based on device viewport width?','@keyframes','@media','@supports','@viewport','B','Beginner','2026-10-06 19:01:32'),(50,10,'How does CSS Grid differ fundamentally from CSS Flexbox?','CSS Grid is one-dimensional; Flexbox is two-dimensional','CSS Grid is two-dimensional (rows & columns); Flexbox is one-dimensional (row or column)','CSS Grid only works on desktop browsers; Flexbox is mobile-only','Flexbox requires JavaScript; CSS Grid is purely declarative','B','Intermediate','2026-10-06 19:01:32'),(51,11,'What is the difference between \'==\' and \'===\' in JavaScript?','\'==\' performs strict comparison; \'===\' allows type coercion','\'===\' checks both value and type without coercion; \'==\' coerces types before comparing','There is no difference in modern ECMAScript','\'===\' is used exclusively for object references','B','Beginner','2026-10-06 19:01:32'),(52,11,'Which keyword declares a block-scoped variable that cannot be reassigned after declaration in JavaScript?','var','let','const','static','C','Beginner','2026-10-06 19:01:32'),(53,11,'What does the JavaScript method \'document.querySelector()\' return if no matching element is found?','undefined','null','false','Empty NodeList','B','Beginner','2026-10-06 19:01:32'),(54,11,'What is the return type of the asynchronous \'fetch()\' API in modern JavaScript?','XMLHttpRequest','Promise','Callback','JSON string','B','Intermediate','2026-10-06 19:01:32'),(55,11,'What mechanism causes an event triggered on a child element to propagate upwards to its parent elements?','Event Hoisting','Event Bubbling','Event Polling','Event Injection','B','Intermediate','2026-10-06 19:01:32'),(56,12,'What is the exact signature of the entry point method in a standard Java application?','public void main(String args[])','public static void main(String[] args)','private static int main(String[] args)','static void main()','B','Beginner','2026-10-06 19:01:32'),(57,12,'What is the default initial value of an uninitialized boolean instance variable in Java?','true','false','0','null','B','Beginner','2026-10-06 19:01:32'),(58,12,'How many bytes does the \'int\' primitive data type occupy in standard Java Virtual Machine (JVM)?','2 bytes','4 bytes','8 bytes','16 bytes','B','Beginner','2026-10-06 19:01:32'),(59,12,'What happens when you compile and run: byte b = 127; b++; in Java?','Compilation error (overflow)','b overflows to -128 due to two\'s complement arithmetic','b becomes 128','A RuntimeException is thrown','B','Intermediate','2026-10-06 19:01:32'),(60,12,'Which Java primitive represents a single 16-bit Unicode character?','byte','short','char','String','C','Beginner','2026-10-06 19:01:32'),(61,13,'Which keyword is used in Java to achieve class inheritance?','implements','inherits','extends','super','C','Beginner','2026-10-06 19:01:32'),(62,13,'What is method overriding in Java?','Defining multiple methods with the same name but different parameter lists in the same class','Providing a specific implementation in a subclass for a method already defined in its superclass','Making a method private so subclasses cannot alter it','Overloading constructors with default arguments','B','Intermediate','2026-10-06 19:01:32'),(63,13,'Which access modifier restricts member visibility strictly to the enclosing class?','public','protected','private','default (package-private)','C','Beginner','2026-10-06 19:01:32'),(64,13,'What is the purpose of the \'super\' keyword in Java?','Allocates memory directly on the hardware stack','Refers to the immediate parent (superclass) object or constructor','Declares an immutable constant variable','Overrides the garbage collection cycle','B','Beginner','2026-10-06 19:01:32'),(65,13,'Can an abstract class in Java have both abstract methods and concrete implemented methods?','No, abstract classes can only contain abstract methods','Yes, abstract classes can contain both abstract and concrete methods','Only if all methods are marked static','Only if the class implements the Serializable interface','B','Intermediate','2026-10-06 19:01:32'),(66,14,'Which interface in Java Collections Framework prevents duplicate elements?','List','Set','Queue','Map','B','Beginner','2026-10-06 19:01:32'),(67,14,'What is the primary difference between ArrayList and LinkedList in Java?','ArrayList uses a dynamic array; LinkedList uses a doubly-linked node list','LinkedList provides O(1) indexed random access; ArrayList does not','ArrayList allows duplicate elements; LinkedList does not','LinkedList is synchronized; ArrayList is not','A','Intermediate','2026-10-06 19:01:32'),(68,14,'What class should be used in Java for key-value pair lookups with O(1) average time complexity?','TreeSet','HashMap','Vector','PriorityQueue','B','Beginner','2026-10-06 19:01:32'),(69,14,'Which interface should a class implement to enable natural sorting with Collections.sort()?','Serializable','Cloneable','Comparable','Iterable','C','Intermediate','2026-10-06 19:01:32'),(70,14,'What happens when you add a duplicate key into a Java HashMap?','A DuplicateKeyException is thrown','The old value associated with the key is overwritten by the new value','The new key-value pair is ignored','The entire map is reset','B','Beginner','2026-10-06 19:01:32'),(71,15,'What is the primary purpose of a Primary Key constraint in a relational table?','Encrypts stored sensitive column values','Uniquely identifies each record/tuple and prohibits NULL values','Enforces alphabetical ordering of query results','Connects tables across distributed network clusters','B','Beginner','2026-10-06 19:01:32'),(72,15,'What does Referential Integrity enforce in a relational database?','Every foreign key value must match an existing primary key value in the referenced table (or be NULL)','Every table must have at least five columns','Indexes must be rebuilt after every transaction','Database passwords must be changed regularly','A','Intermediate','2026-10-06 19:01:32'),(73,15,'In Entity-Relationship (ER) modeling, what does a diamond symbol traditionally represent?','An Entity set','An Attribute','A Relationship set','A Weak Entity','C','Beginner','2026-10-06 19:01:32'),(74,15,'What is a composite key in relational database design?','A primary key composed of two or more columns combined together','A key that automatically decrypts database fields','A key created using artificial auto-increment numbers','A foreign key that references multiple remote databases','A','Beginner','2026-10-06 19:01:32'),(75,15,'Which ACID property guarantees that all operations in a database transaction succeed or all are rolled back?','Atomicity','Consistency','Isolation','Durability','A','Intermediate','2026-10-06 19:01:32'),(76,16,'What is the difference between WHERE and HAVING clauses in SQL?','WHERE filters rows before aggregation; HAVING filters aggregated groups','HAVING is used for string patterns; WHERE is used for numbers','WHERE can only be used with SELECT; HAVING is used with UPDATE','There is no functional difference in SQL standards','A','Intermediate','2026-10-06 19:01:32'),(77,16,'Which SQL JOIN returns all records from the left table and matching records from the right table (filling NULLs for non-matches)?','INNER JOIN','LEFT JOIN','RIGHT JOIN','CROSS JOIN','B','Beginner','2026-10-06 19:01:32'),(78,16,'Which aggregate function counts the total number of non-null rows matching a condition in SQL?','SUM()','COUNT()','TOTAL()','ROWS()','B','Beginner','2026-10-06 19:01:32'),(79,16,'What clause is used in SQL to eliminate duplicate rows from a query result set?','GROUP ALL','UNIQUE','DISTINCT','FILTER DUPES','C','Beginner','2026-10-06 19:01:32'),(80,16,'What is the result of an INNER JOIN between two tables if no rows satisfy the ON condition?','All rows from both tables with NULLs','An empty result set (0 rows)','A SQL syntax error','A Cartesian product of all rows','B','Beginner','2026-10-06 19:01:32'),(81,17,'What is the primary condition for a relation to be in First Normal Form (1NF)?','Every column value must be atomic (indivisible) with no repeating groups','All transitive dependencies must be removed','The relation must have at least two candidate keys','Every foreign key must reference an index','A','Intermediate','2026-10-06 19:01:32'),(82,17,'A relation in 1NF is in Second Normal Form (2NF) if and only if it has no:','Multivalued dependencies','Partial dependencies (non-prime attributes fully dependent on the whole candidate key)','Transitive dependencies','Foreign key constraints','B','Intermediate','2026-10-06 19:01:32'),(83,17,'What does Third Normal Form (3NF) eliminate from a relational schema?','Atomic attributes','Transitive functional dependencies','Primary keys','Candidate keys','B','Intermediate','2026-10-06 19:01:32'),(84,17,'What is the main objective of database schema normalization?','To minimize data redundancy and eliminate update/delete/insert anomalies','To maximize the physical storage size on the disk','To reduce the number of SQL queries required for reports','To merge all database tables into a single large sheet','A','Beginner','2026-10-06 19:01:32'),(85,17,'How is Boyce-Codd Normal Form (BCNF) stricter than standard 3NF?','In BCNF, for every functional dependency X -> Y, X must be a superkey','BCNF permits partial dependencies on composite keys','BCNF only applies to NoSQL document collections','BCNF requires that all attributes be integers','A','Advanced','2026-10-06 19:01:32'),(86,18,'How many architectural layers are defined in the standard ISO/OSI Reference Model?','4','5','7','9','C','Beginner','2026-10-06 19:01:32'),(87,18,'At which OSI layer do Network Routers operate to perform packet forwarding and path selection?','Layer 2 (Data Link Layer)','Layer 3 (Network Layer)','Layer 4 (Transport Layer)','Layer 7 (Application Layer)','B','Beginner','2026-10-06 19:01:32'),(88,18,'What is the Protocol Data Unit (PDU) at the Data Link Layer called?','Bit','Frame','Packet','Segment','B','Beginner','2026-10-06 19:01:32'),(89,18,'Which OSI layer is responsible for end-to-end communication, segmentation, flow control, and error recovery?','Physical Layer','Network Layer','Transport Layer','Presentation Layer','C','Beginner','2026-10-06 19:01:32'),(90,18,'Which layer of the OSI model handles data encryption, decryption, and compression?','Application Layer','Presentation Layer','Session Layer','Transport Layer','B','Intermediate','2026-10-06 19:01:32'),(91,19,'How many bits comprise a standard IPv4 address?','16 bits','32 bits','64 bits','128 bits','B','Beginner','2026-10-06 19:01:32'),(92,19,'In CIDR notation, how many usable host IP addresses are provided by a /24 subnet (e.g. 192.168.1.0/24)?','256','254 (excluding network and broadcast addresses)','128','512','B','Intermediate','2026-10-06 19:01:32'),(93,19,'What is the standard loopback IP address in IPv4 networking?','192.168.0.1','10.0.0.1','127.0.0.1','255.255.255.255','C','Beginner','2026-10-06 19:01:32'),(94,19,'Which IP address range is designated for Class A Private Networks under RFC 1918?','10.0.0.0 to 10.255.255.255','172.16.0.0 to 172.31.255.255','192.168.0.0 to 192.168.255.255','169.254.0.0 to 169.254.255.255','A','Intermediate','2026-10-06 19:01:32'),(95,19,'How many bits comprise a next-generation IPv6 address?','32 bits','64 bits','128 bits','256 bits','C','Beginner','2026-10-06 19:01:32'),(96,20,'What sequence of packets completes the reliable TCP 3-Way Handshake?','SYN -> SYN-ACK -> ACK','ACK -> SYN -> SYN-ACK','FIN -> ACK -> FIN-ACK','SYN -> ACK -> DATA','A','Intermediate','2026-10-06 19:01:32'),(97,20,'Why is UDP preferred over TCP for live video streaming and online gaming?','UDP performs extensive retransmissions of lost packets','UDP is connectionless and has minimal transmission overhead without handshake delay','UDP encrypts all packet payloads automatically','UDP has built-in congestion control algorithms','B','Intermediate','2026-10-06 19:01:32'),(98,20,'What standard port number is assigned by IANA for secure HTTPS web traffic?','21','53','80','443','D','Beginner','2026-10-06 19:01:32'),(99,20,'Which protocol translates human-readable domain names (e.g. google.com) into numerical IP addresses?','DHCP','DNS','ARP','ICMP','B','Beginner','2026-10-06 19:01:32'),(100,20,'What mechanism does TCP use to prevent a fast sender from overwhelming a slow receiver\'s buffer?','Checksum Calculation','Flow Control via Sliding Window','Packet Fragmentation','Routing Updates','B','Intermediate','2026-10-06 19:01:32'),(101,21,'What data structure is maintained by the operating system kernel to store all attributes of a process?','File Allocation Table (FAT)','Process Control Block (PCB)','Translation Lookaside Buffer (TLB)','Interrupt Vector Table','B','Beginner','2026-10-06 19:01:32'),(102,21,'What happens during an operating system Context Switch?','The CPU executes garbage collection','The state of the currently running process is saved and the state of another process is restored to CPU registers','A process is permanently terminated and its files are unlinked','Virtual memory pages are wiped to zeros','B','Intermediate','2026-10-06 19:01:32'),(103,21,'Which system call is invoked in POSIX/Unix operating systems to create a new child process?','exec()','fork()','wait()','clone()','B','Beginner','2026-10-06 19:01:32'),(104,21,'What is the key difference between a Process and a Thread?','Processes share memory by default; Threads have isolated memory','Threads within the same process share the same memory space; Processes have isolated address spaces','Threads cannot run concurrently on multi-core processors','Processes have lower context-switching overhead than threads','B','Intermediate','2026-10-06 19:01:32'),(105,21,'What is a Zombie Process in Unix-like operating systems?','A process that runs endlessly in an infinite loop consuming 100% CPU','A process that has finished execution but still has an entry in the process table because its parent has not read its exit status','A malicious process that spreads via network sockets','A process whose parent process died before it started','B','Intermediate','2026-10-06 19:01:32'),(106,22,'What phenomenon occurs in First-Come First-Served (FCFS) scheduling when short processes wait behind a long CPU-bound process?','Starvation','Convoy Effect','Priority Inversion','Belady\'s Anomaly','B','Intermediate','2026-10-06 19:01:32'),(107,22,'Which CPU scheduling algorithm provides the theoretical minimum average waiting time for a given set of processes?','First-Come First-Served (FCFS)','Shortest Job First (SJF)','Round Robin (RR)','Multi-Level Feedback Queue','B','Intermediate','2026-10-06 19:01:32'),(108,22,'What critical parameter determines the behavior of the Round Robin (RR) CPU scheduling algorithm?','Memory Page Size','Time Quantum (Slice)','Cache Line Size','Disk Sector Size','B','Beginner','2026-10-06 19:01:32'),(109,22,'What is Starvation in CPU scheduling, and what technique is commonly used to prevent it?','Low priority processes never execute; prevented by Aging (gradually increasing priority)','A CPU overheating condition; prevented by lowering clock frequency','Deadlock between two processes; prevented by Semaphores','Memory fragmentation; prevented by Paging','A','Intermediate','2026-10-06 19:01:32'),(110,22,'In preemptive scheduling, what can cause a currently running process to yield the CPU before completing its CPU burst?','The process voluntarily makes an I/O request','A higher-priority process arrives or a timer interrupt expires','The process reaches its exit() system call','The operating system halts completely','B','Intermediate','2026-10-06 19:01:32'),(111,23,'What is the primary role of Paging in operating systems memory management?','Allows physical address space of a process to be non-contiguous, eliminating external fragmentation','Encrypts RAM storage chips against hardware tampering','Synchronizes hard drive sectors with CPU registers','Limits all processes to exactly 64KB of RAM','A','Intermediate','2026-10-06 19:01:32'),(112,23,'What hardware component translates Virtual Memory addresses to Physical RAM addresses using page tables?','Arithmetic Logic Unit (ALU)','Memory Management Unit (MMU)','Direct Memory Access (DMA) Controller','PCIe Controller','B','Intermediate','2026-10-06 19:01:32'),(113,23,'What is a Page Fault in virtual memory systems?','A physical hardware error in a RAM chip','An interrupt raised when a program accesses a page that is mapped in virtual address space but not loaded in physical RAM','A memory leak caused by unclosed file descriptors','A syntax error in assembly language instructions','B','Intermediate','2026-10-06 19:01:32'),(114,23,'What is the difference between Internal and External Fragmentation?','Internal occurs within allocated blocks; External occurs between unallocated free memory blocks','Internal occurs on hard drives; External occurs on RAM','Internal is caused by CPU caches; External is caused by network cards','There is no difference in operating system design','A','Intermediate','2026-10-06 19:01:32'),(115,23,'What condition is termed \'Thrashing\' in an operating system?','CPU running at 100% capacity on mathematical calculations','The system spends more time swapping pages into and out of disk than executing useful user processes','A deadlock involving four or more mutual exclusions','A sudden kernel panic caused by power failure','B','Advanced','2026-10-06 19:01:32');
/*!40000 ALTER TABLE `quizzes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resources`
--

DROP TABLE IF EXISTS `resources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `resources` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topic_id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `resource_type` varchar(50) NOT NULL,
  `url` varchar(500) NOT NULL,
  `description` text DEFAULT NULL,
  `difficulty` varchar(30) NOT NULL DEFAULT 'Beginner',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_resources_topic` (`topic_id`),
  CONSTRAINT `fk_resources_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resources`
--

LOCK TABLES `resources` WRITE;
/*!40000 ALTER TABLE `resources` DISABLE KEYS */;
INSERT INTO `resources` VALUES (1,1,'Python Official Documentation: Data Types','Documentation','https://docs.python.org/3/tutorial/introduction.html','Official Python guide covering numbers, strings, and list indexing fundamentals.','Beginner','2026-10-06 05:48:51'),(2,1,'Understanding Python Variable Scoping','Article','https://realpython.com/python-variables/','Comprehensive article explaining variable assignment, dynamic typing, and object references.','Beginner','2026-10-06 05:48:51'),(3,1,'Interactive Data Types Exercises','Practice','https://www.w3schools.com/python/python_datatypes.asp','Self-paced code challenges and syntax quizzes on Python data types.','Beginner','2026-10-06 05:48:51'),(4,2,'Python Control Flow Guide','Documentation','https://docs.python.org/3/tutorial/controlflow.html','Official guide on if statements, for loops, and the range() function.','Beginner','2026-10-06 05:48:51'),(5,2,'Python Loops and Branching Notes','Notes','https://realpython.com/python-conditional-statements/','Detailed study notes on boolean conditions and loop control keywords (break, continue).','Beginner','2026-10-06 05:48:51'),(6,3,'Defining Functions in Python','Documentation','https://docs.python.org/3/tutorial/controlflow.html#defining-functions','In-depth guide on defining functions, default arguments, and lambda expressions.','Intermediate','2026-10-06 05:48:51'),(7,3,'Python Modular Programming & Packages','Article','https://realpython.com/python-modules-packages/','Tutorial on structuring reusable Python modules and packages.','Intermediate','2026-10-06 05:48:51'),(8,4,'Linked List Fundamentals & Node Structures','Notes','https://www.geeksforgeeks.org/data-structures/linked-list/','Curated notes on singly, doubly, and circular linked lists with pointer tracing.','Beginner','2026-10-06 05:48:51'),(9,4,'Array Memory Layout and Big-O Complexity','Article','https://www.geeksforgeeks.org/array-data-structure/','Deep dive into array indexing speed, memory cache locality, and algorithmic trade-offs.','Beginner','2026-10-06 05:48:51'),(10,4,'Linked List Implementation Practice','Practice','https://leetcode.com/explore/learn/card/linked-list/','Interactive coding challenges focusing on linked list reversal and node insertion.','Intermediate','2026-10-06 05:48:51'),(11,5,'Stack and Queue ADT Specification','Documentation','https://www.geeksforgeeks.org/stack-data-structure/','Formal abstract data type definitions, LIFO/FIFO invariants, and array/list implementations.','Intermediate','2026-10-06 05:48:51'),(12,5,'Balanced Parentheses & Monotonic Stack Notes','Notes','https://cp-algorithms.com/data_structures/stack_queue_modification.html','Study notes on classic stack interview applications and monotonic queue patterns.','Intermediate','2026-10-06 05:48:51'),(13,6,'MDN Web Docs: HTML Basics','Documentation','https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics','Mozilla Developer Network foundational tutorial on HTML elements and page structuring.','Beginner','2026-10-06 05:48:51'),(14,6,'Semantic HTML Elements and Web Accessibility','Article','https://developer.mozilla.org/en-US/docs/Glossary/Semantics','Guide to choosing semantic elements (article, section, nav) for accessibility.','Beginner','2026-10-06 05:48:51'),(15,10,'MDN Guide to CSS Flexbox','Documentation','https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Flexbox','Comprehensive guide to flexible box layouts, axis directions, and alignment properties.','Beginner','2026-10-06 05:48:51'),(16,10,'A Complete Guide to CSS Grid','Article','https://css-tricks.com/snippets/css/complete-guide-grid/','Visual reference for grid container properties and track alignments.','Intermediate','2026-10-06 05:48:51'),(17,13,'Oracle Java Tutorials: Object-Oriented Programming','Documentation','https://docs.oracle.com/javase/tutorial/java/concepts/','Official Oracle tutorials explaining classes, objects, interfaces, and inheritance.','Intermediate','2026-10-06 05:48:51'),(18,13,'Java OOP Best Practices & Encapsulation','Article','https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/','Practical guide on constructors, access modifiers, and SOLID design principles.','Intermediate','2026-10-06 05:48:51'),(19,16,'PostgreSQL / MySQL SELECT and JOIN Reference','Documentation','https://dev.mysql.com/doc/refman/8.0/en/select.html','Official SQL syntax reference for joins, aggregations, and grouping clauses.','Intermediate','2026-10-06 05:48:51'),(20,16,'Visual Explanation of SQL Joins','Notes','https://blog.codinghorror.com/a-visual-explanation-of-sql-joins/','Intuitive Venn diagrams and record matching examples for inner, outer, and cross joins.','Beginner','2026-10-06 05:48:51'),(21,16,'Interactive SQL Practice Sandbox','Practice','https://sqlzoo.net/','Hands-on browser-based SQL exercises with real table schemas and automated feedback.','Intermediate','2026-10-06 05:48:51'),(22,18,'Cloudflare Learning: The OSI 7-Layer Model','Article','https://www.cloudflare.com/learning/ddos/glossary/open-systems-interconnection-model-osi/','Clear breakdown of physical, data link, network, transport, session, presentation, and application layers.','Beginner','2026-10-06 05:48:51'),(23,18,'TCP/IP Protocol Suite Study Notes','Notes','https://www.geeksforgeeks.org/tcp-ip-model/','Comparison table between OSI 7 layers and the 4 TCP/IP layers with protocol examples.','Beginner','2026-10-06 05:48:51'),(24,22,'OSTEP: CPU Scheduling Principles','Notes','https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf','Free textbook chapter from \'Operating Systems: Three Easy Pieces\' on scheduling policies.','Intermediate','2026-10-06 05:48:51'),(25,22,'Comparative Analysis of SJF, Round Robin, and Multi-Level Queue','Article','https://www.geeksforgeeks.org/cpu-scheduling-in-operating-systems/','Detailed breakdown of turnaround time, waiting time, and preemptive context overhead.','Intermediate','2026-10-06 05:48:51');
/*!40000 ALTER TABLE `resources` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_profiles`
--

DROP TABLE IF EXISTS `student_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `student_profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `education_level` varchar(50) DEFAULT NULL,
  `course` varchar(100) DEFAULT NULL,
  `semester` varchar(20) DEFAULT NULL,
  `skill_level` varchar(30) DEFAULT NULL,
  `learning_goal` text DEFAULT NULL,
  `preferred_study_time` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_student_profiles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=251 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_profiles`
--

LOCK TABLES `student_profiles` WRITE;
/*!40000 ALTER TABLE `student_profiles` DISABLE KEYS */;
INSERT INTO `student_profiles` VALUES (186,2019,'Undergraduate','B.Tech','Semester 7, Year 4,','Intermediate','Software Developer','Night (9 PM - 2 AM)','2026-10-08 08:43:49','2026-10-08 08:43:49');
/*!40000 ALTER TABLE `student_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `study_plan_items`
--

DROP TABLE IF EXISTS `study_plan_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `study_plan_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `study_plan_id` int(11) NOT NULL,
  `day_number` int(11) NOT NULL,
  `topic_id` int(11) NOT NULL,
  `task` text NOT NULL,
  `completed` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_plan_items_plan` (`study_plan_id`),
  KEY `idx_plan_items_topic` (`topic_id`),
  CONSTRAINT `fk_plan_items_plan` FOREIGN KEY (`study_plan_id`) REFERENCES `study_plans` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_plan_items_topic` FOREIGN KEY (`topic_id`) REFERENCES `topics` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1824 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `study_plan_items`
--

LOCK TABLES `study_plan_items` WRITE;
/*!40000 ALTER TABLE `study_plan_items` DISABLE KEYS */;
INSERT INTO `study_plan_items` VALUES (1601,472,1,12,'Applied Implementation: Study working examples, write practice code/solutions, and test edge cases for \'Java Syntax & Primitive Types\'. (Morning study session)',1,'2026-10-12 09:31:55'),(1602,472,2,13,'Applied Implementation: Study working examples, write practice code/solutions, and test edge cases for \'Classes & Object-Oriented Principles\'. (Morning study session)',1,'2026-10-12 09:31:55'),(1603,472,3,14,'Applied Implementation: Study working examples, write practice code/solutions, and test edge cases for \'Java Collections Framework\'. (Morning study session)',1,'2026-10-12 09:31:55'),(1604,472,4,12,'Targeted Practice: Re-solve challenging problems and debug edge cases for \'Java Syntax & Primitive Types\'.',1,'2026-10-12 09:31:55'),(1605,472,5,13,'Targeted Practice: Re-solve challenging problems and debug edge cases for \'Classes & Object-Oriented Principles\'.',1,'2026-10-12 09:31:55'),(1606,472,6,14,'Targeted Practice: Re-solve challenging problems and debug edge cases for \'Java Collections Framework\'.',1,'2026-10-12 09:31:55'),(1607,472,7,12,'Milestone Assessment: Synthesize curriculum knowledge in Java Programming and complete an applied mini-project/problem set aligned with your goal: \'Software Developer\'.',1,'2026-10-12 09:31:55');
/*!40000 ALTER TABLE `study_plan_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `study_plans`
--

DROP TABLE IF EXISTS `study_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `study_plans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `goal` text NOT NULL,
  `duration_days` int(11) NOT NULL DEFAULT 7,
  `skill_level` varchar(30) NOT NULL DEFAULT 'Beginner',
  `preferred_study_time` varchar(50) NOT NULL DEFAULT 'Flexible',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_study_plans_user` (`user_id`),
  KEY `idx_study_plans_subject` (`subject_id`),
  CONSTRAINT `fk_study_plans_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_study_plans_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=536 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `study_plans`
--

LOCK TABLES `study_plans` WRITE;
/*!40000 ALTER TABLE `study_plans` DISABLE KEYS */;
INSERT INTO `study_plans` VALUES (472,2019,7,'Software Developer',7,'Intermediate','Morning','2026-10-12 09:31:55');
/*!40000 ALTER TABLE `study_plans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subjects`
--

DROP TABLE IF EXISTS `subjects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `subjects` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subjects`
--

LOCK TABLES `subjects` WRITE;
/*!40000 ALTER TABLE `subjects` DISABLE KEYS */;
INSERT INTO `subjects` VALUES (1,'Python Programming','Fundamental and advanced concepts of Python programming language including syntax, data structures, and modular design.','2026-10-06 05:34:59'),(2,'Data Structures & Algorithms','Core data structures, algorithm analysis, recursion, sorting, searching, and algorithmic problem-solving paradigms.','2026-10-06 05:34:59'),(3,'Web Development Basics','Foundations of modern frontend development: HTML5 semantic markup, CSS3 styling, responsive layouts, and JavaScript fundamentals.','2026-10-06 05:34:59'),(7,'Java Programming','Object-oriented programming using Java: strong typing, classes, inheritance, polymorphism, exception handling, and collections.','2026-10-06 05:48:51'),(8,'Database Management Systems','Relational database concepts, ER modeling, SQL querying, schema normalization, ACID transactions, and index optimization.','2026-10-06 05:48:51'),(9,'Computer Networks','Principles of computer communications: OSI and TCP/IP protocol stacks, IP addressing, routing, transport layer protocols, and sockets.','2026-10-06 05:48:51'),(10,'Operating Systems','Internal architecture of operating systems: process scheduling, inter-process communication, multithreading, and memory paging.','2026-10-06 05:48:51');
/*!40000 ALTER TABLE `subjects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `topics`
--

DROP TABLE IF EXISTS `topics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `topics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subject_id` int(11) NOT NULL,
  `topic_name` varchar(150) NOT NULL,
  `description` text DEFAULT NULL,
  `difficulty` varchar(30) NOT NULL DEFAULT 'Beginner',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_topics_subject` (`subject_id`),
  CONSTRAINT `fk_topics_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `topics`
--

LOCK TABLES `topics` WRITE;
/*!40000 ALTER TABLE `topics` DISABLE KEYS */;
INSERT INTO `topics` VALUES (1,1,'Variables & Data Types','Numbers, strings, booleans, lists, dictionaries, tuples, and type casting in Python.','Beginner','2026-10-06 05:34:59'),(2,1,'Control Structures','Conditional branching with if-elif-else, while loops, and for loops with range.','Beginner','2026-10-06 05:34:59'),(3,1,'Functions & Modules','Defining functions, positional/keyword arguments, return values, scope, and importing standard libraries.','Intermediate','2026-10-06 05:34:59'),(4,2,'Arrays & Linked Lists','Contiguous arrays vs node-based singly and doubly linked lists, operations and time complexities.','Beginner','2026-10-06 05:34:59'),(5,2,'Stacks & Queues','LIFO and FIFO data structures, stack-based expression evaluation, queue buffers, and deque.','Intermediate','2026-10-06 05:34:59'),(6,3,'Semantic HTML & Document Structure','HTML5 document structure, semantic tags, forms, input types, and accessibility guidelines.','Beginner','2026-10-06 05:34:59'),(7,1,'Lists, Tuples & Sets','Sequential collection operations, indexing, slicing, comprehensions, and set algebra in Python.','Beginner','2026-10-06 05:48:51'),(8,1,'Dictionaries & Hash Maps','Key-value pair mappings, dictionary methods, nested dictionaries, and frequency counting.','Intermediate','2026-10-06 05:48:51'),(9,2,'Binary Trees & BST','Hierarchical tree nodes, in-order/pre-order traversals, and binary search tree lookup/insertion.','Advanced','2026-10-06 05:48:51'),(10,3,'CSS Layouts & Responsive Design','Box model, Flexbox alignment, CSS Grid, media queries, and responsive viewport design.','Beginner','2026-10-06 05:48:51'),(11,3,'JavaScript Fundamentals','Variables, arrow functions, DOM manipulation, event listeners, and asynchronous fetch requests.','Intermediate','2026-10-06 05:48:51'),(12,7,'Java Syntax & Primitive Types','Java main method, primitive types, operators, variable declarations, and type casting.','Beginner','2026-10-06 05:48:51'),(13,7,'Classes & Object-Oriented Principles','Class definitions, constructors, encapsulation, getters/setters, inheritance, and method overriding.','Intermediate','2026-10-06 05:48:51'),(14,7,'Java Collections Framework','List, Set, Map interfaces, ArrayList, HashMap, and standard iteration patterns.','Intermediate','2026-10-06 05:48:51'),(15,8,'Database Fundamentals & ER Model','Relational database concepts, tables, primary/foreign keys, entity-relationship diagrams, and cardinality.','Beginner','2026-10-06 05:48:51'),(16,8,'SQL Queries & Joins','SELECT queries, WHERE filtering, GROUP BY aggregations, INNER/LEFT/RIGHT JOINs, and subqueries.','Intermediate','2026-10-06 05:48:51'),(17,8,'Normalization & Normal Forms','Data redundancy elimination, 1NF, 2NF, 3NF, BCNF, functional dependencies, and lossless joins.','Advanced','2026-10-06 05:48:51'),(18,9,'Network Fundamentals & OSI Model','Network topologies, layered architectures, the 7-layer OSI model, and the 4-layer TCP/IP suite.','Beginner','2026-10-06 05:48:51'),(19,9,'IP Addressing & Subnetting','IPv4 classless addressing, CIDR notation, subnet masks, network vs host IDs, and IPv6 overview.','Intermediate','2026-10-06 05:48:51'),(20,9,'TCP/IP & Transport Protocols','Reliable TCP 3-way handshake, flow control, congestion control, and connectionless UDP.','Intermediate','2026-10-06 05:48:51'),(21,10,'Processes & Process Management','Process control blocks (PCB), process state transitions, context switching, and fork/exec lifecycles.','Beginner','2026-10-06 05:48:51'),(22,10,'CPU Scheduling Algorithms','First-Come First-Served (FCFS), Shortest Job First (SJF), Round Robin (RR), and Priority Scheduling.','Intermediate','2026-10-06 05:48:51'),(23,10,'Memory Management & Virtual Memory','Paging, segmentation, page tables, page faults, and virtual memory swap mechanics.','Advanced','2026-10-06 05:48:51');
/*!40000 ALTER TABLE `topics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(191) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'student',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2932 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (2019,'Subham Kumar Dash','subhamkumardash000@gmail.com','scrypt:32768:8:1$FZ4JABiPCZ9uO2gK$8098251ad8e61a5c7effe2ee87afc9d95391bf38ad951845d7301fb61c45332bb7efde7bd83b4ae3913b632f2312727078c7a544ad8ac16be29406b03eece167','student','2026-10-08 08:41:13');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'edumentor_ai'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-13  3:59:17
