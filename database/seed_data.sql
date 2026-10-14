-- =====================================================================
-- AI Student Learning Mentor - Seed Data
-- Educational subjects, syllabus topics, and verified learning resources.
-- Note: NO fake users, NO fake student profiles, NO fake progress, and
-- NO fake quiz attempts are inserted.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Subjects
-- ---------------------------------------------------------------------
INSERT IGNORE INTO `subjects` (`id`, `name`, `description`) VALUES
(1, 'Python Programming', 'Fundamental and advanced concepts of Python programming language including syntax, data structures, and modular design.'),
(2, 'Data Structures & Algorithms', 'Core data structures, algorithm analysis, recursion, sorting, searching, and algorithmic problem-solving paradigms.'),
(3, 'Web Development Basics', 'Foundations of modern frontend development: HTML5 semantic markup, CSS3 styling, responsive layouts, and JavaScript fundamentals.'),
(4, 'Java Programming', 'Object-oriented programming using Java: strong typing, classes, inheritance, polymorphism, exception handling, and collections.'),
(5, 'Database Management Systems', 'Relational database concepts, ER modeling, SQL querying, schema normalization, ACID transactions, and index optimization.'),
(6, 'Computer Networks', 'Principles of computer communications: OSI and TCP/IP protocol stacks, IP addressing, routing, transport layer protocols, and sockets.'),
(7, 'Operating Systems', 'Internal architecture of operating systems: process scheduling, inter-process communication, multithreading, and memory paging.');

-- ---------------------------------------------------------------------
-- 2. Syllabus Topics
-- ---------------------------------------------------------------------
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

-- ---------------------------------------------------------------------
-- 3. Verified Educational Resources
-- ---------------------------------------------------------------------
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
(24, 22, 'OSTEP: CPU Scheduling Principles', 'Notes', 'https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf', 'Free textbook chapter from ''Operating Systems: Three Easy Pieces'' on scheduling policies.', 'Intermediate'),
(25, 22, 'Comparative Analysis of SJF, Round Robin, and Multi-Level Queue', 'Article', 'https://www.geeksforgeeks.org/cpu-scheduling-in-operating-systems/', 'Detailed breakdown of turnaround time, waiting time, and preemptive context overhead.', 'Intermediate'),
(26, 19, 'Cisco IP Addressing and Subnetting Guide', 'Documentation', 'https://www.geeksforgeeks.org/ip-addressing-introduction-and-classful-addressing/', 'Technical reference covering IPv4 address structures, classful networks, subnet masks, and network prefix calculation.', 'Intermediate'),
(27, 19, 'Introduction to Subnetting & CIDR Notation', 'Notes', 'https://www.geeksforgeeks.org/introduction-to-subnetting/', 'Concise study notes on determining network IDs, host ranges, broadcast addresses, and variable-length subnet masks.', 'Intermediate'),
(28, 19, 'Interactive Subnetting Practice Sandbox', 'Practice', 'https://www.subnetting.org/', 'Online speed drills and interactive exercises to master subnetting math and CIDR prefix conversions.', 'Intermediate'),
(29, 19, 'Crash Course Computer Science: Networks & Subnets', 'Video', 'https://www.youtube.com/watch?v=3QhU9jd03a0', 'Illustrated video lecture explaining packets, routing, IP addresses, and how data travels across the Internet.', 'Beginner'),
(30, 20, 'RFC 793: Transmission Control Protocol Specification', 'Documentation', 'https://www.ietf.org/rfc/rfc793.txt', 'Official IETF protocol standard defining TCP states, three-way handshakes, sequence numbers, and packet acknowledgment.', 'Intermediate'),
(31, 20, 'Key Differences Between TCP and UDP Protocols', 'Notes', 'https://www.geeksforgeeks.org/differences-between-tcp-and-udp/', 'Structured comparative notes on connection-oriented reliable byte streams vs connectionless unreliable datagrams.', 'Intermediate'),
(32, 20, 'Cloudflare Learning: What is TCP and How Flow Control Works', 'Article', 'https://www.cloudflare.com/learning/ddos/glossary/transmission-control-protocol-tcp/', 'Comprehensive article explaining sliding windows, congestion control algorithms, and port multiplexing.', 'Intermediate'),
(33, 20, 'GeeksforGeeks Transport Layer Multiple-Choice Quiz', 'Practice', 'https://www.geeksforgeeks.org/computer-network-quizzes/', 'Practice multiple-choice questions assessing understanding of TCP handshake, port assignments, and UDP headers.', 'Intermediate'),
(34, 9, 'Binary Search Tree (BST) Properties and Operations', 'Documentation', 'https://www.geeksforgeeks.org/binary-search-tree-data-structure/', 'Reference guide detailing BST invariants, recursive insertion, deletion cases, and search complexity analysis.', 'Advanced'),
(35, 9, 'Tree Traversals: Preorder, Inorder, and Postorder Notes', 'Notes', 'https://www.geeksforgeeks.org/tree-traversals-inorder-preorder-and-postorder/', 'Concise notes on depth-first search orderings, breadth-first level order traversal, and call-stack visualization.', 'Intermediate'),
(36, 9, 'LeetCode Explore: Introduction to Binary Search Trees', 'Practice', 'https://leetcode.com/explore/learn/card/introduction-to-data-structure-binary-search-tree/', 'Interactive coding track covering BST validation, lowest common ancestor, and balanced tree implementations.', 'Advanced'),
(37, 9, 'freeCodeCamp: Binary Search Trees Tutorial', 'Video', 'https://www.youtube.com/watch?v=fAAZ23xIC3s', 'Visual animated video walkthrough explaining binary tree node representation, recursion, and search algorithms.', 'Intermediate'),
(38, 15, 'Entity-Relationship (ER) Modeling Concepts', 'Documentation', 'https://www.geeksforgeeks.org/introduction-of-er-model/', 'Foundational guide to entities, weak entity sets, attributes, primary keys, relationships, and cardinality mapping.', 'Beginner'),
(39, 15, 'Relational Model and ER-to-Relational Mapping Notes', 'Notes', 'https://www.guru99.com/er-diagram-tutorial-dbms.html', 'Study notes detailing how conceptual ER diagrams translate into foreign keys, relational schemas, and join tables.', 'Beginner'),
(40, 15, 'Lucidchart Guide to ER Diagram Notations', 'Article', 'https://www.lucidchart.com/pages/er-diagrams', 'Visual guide illustrating Chen notation, Crow''s Foot notation, and real-world database design practices.', 'Beginner'),
(41, 15, 'freeCodeCamp: Database Design & Relational Modeling Course', 'Video', 'https://www.youtube.com/watch?v=HXV3zeQKqGY', 'Comprehensive video tutorial covering database schemas, primary keys, foreign key constraints, and relational architecture.', 'Beginner'),
(42, 17, 'Database Normalization: 1NF, 2NF, 3NF, and BCNF Reference', 'Documentation', 'https://www.geeksforgeeks.org/database-normalization-introduction/', 'Formal reference on functional dependencies, prime attributes, candidate keys, and multi-valued dependencies.', 'Advanced'),
(43, 17, 'Worked Normalization Examples and Anomaly Elimination Notes', 'Notes', 'https://www.guru99.com/database-normalization.html', 'Practical examples decomposing unnormalized student and order tables into First, Second, and Third Normal Form.', 'Intermediate'),
(44, 17, 'W3Schools SQL Normalization and Schema Quiz', 'Practice', 'https://www.w3schools.com/sql/sql_quiz.asp', 'Interactive assessment testing comprehension of candidate keys, transitive dependencies, and redundancy prevention.', 'Advanced'),
(45, 17, 'Understanding Boyce-Codd Normal Form (BCNF) and Lossless Joins', 'Article', 'https://www.geeksforgeeks.org/boyce-codd-normal-form-bcnf/', 'Deep dive into BCNF decomposition criteria, dependency preservation trade-offs, and lossless join verification.', 'Advanced'),
(46, 12, 'Oracle Java Tutorials: Primitive Data Types', 'Documentation', 'https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html', 'Official Oracle guide explaining integer types (byte, short, int, long), floating point, boolean, char, and default values.', 'Beginner'),
(47, 12, 'Java Variables, Literals, and Type Casting Notes', 'Notes', 'https://www.geeksforgeeks.org/variables-in-java/', 'Concise notes explaining variable scope (local, instance, static), literal notations, and widening/narrowing type conversions.', 'Beginner'),
(48, 12, 'W3Schools Interactive Java Syntax & Types Exercises', 'Practice', 'https://www.w3schools.com/java/java_syntax.asp', 'Hands-on browser-based exercises for practicing basic Java program structure, print statements, and variable declarations.', 'Beginner'),
(49, 12, 'freeCodeCamp: Java Programming for Beginners', 'Video', 'https://www.youtube.com/watch?v=A74TOX803D0', 'Complete beginner-friendly video walkthrough covering Java installation, compilation, primitive data types, and syntax.', 'Beginner'),
(50, 14, 'Oracle Java Documentation: Collections Framework Overview', 'Documentation', 'https://docs.oracle.com/javase/8/docs/technotes/guides/collections/overview.html', 'Official architectural specification for the java.util collection interfaces: Collection, List, Set, Queue, and Map.', 'Intermediate'),
(51, 14, 'Comprehensive Guide to Java Collections: ArrayList, HashSet, HashMap', 'Article', 'https://www.geeksforgeeks.org/collections-in-java-2/', 'Detailed tutorial on choosing the right collection, iterator implementations, sorting with Comparable/Comparator, and thread safety.', 'Intermediate'),
(52, 14, 'HackerRank Java Data Structures and Collections Practice', 'Practice', 'https://www.hackerrank.com/domains/java?filters%5Bsubdomains%5D%5B%5D=java-data-structures', 'Interactive coding track testing algorithmic manipulation of ArrayLists, 2D arrays, HashSets, and HashMaps in Java.', 'Intermediate'),
(53, 14, 'Java Generics and Collection Complexity Cheat Sheet', 'Notes', 'https://www.geeksforgeeks.org/time-complexity-of-java-collections/', 'Time and space complexity table comparing search, insertion, and deletion Big-O metrics across all major Java collection types.', 'Intermediate'),
(54, 21, 'Process Management in Operating Systems: States and PCB Notes', 'Notes', 'https://www.geeksforgeeks.org/introduction-of-process-management/', 'Study notes covering the five-state process model (New, Ready, Running, Waiting, Terminated) and Process Control Block structure.', 'Beginner'),
(55, 21, 'OSTEP: Process Abstraction and System Call API', 'Documentation', 'https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-intro.pdf', 'Textbook chapter from Operating Systems: Three Easy Pieces detailing fork(), exec(), wait(), and address space duplication.', 'Intermediate'),
(56, 21, 'Inter-Process Communication (IPC): Shared Memory vs Message Passing', 'Article', 'https://www.geeksforgeeks.org/inter-process-communication-ipc/', 'Analysis of IPC mechanisms including anonymous pipes, named pipes (FIFOs), message queues, and shared memory segments.', 'Intermediate'),
(57, 21, 'Crash Course Computer Science: Operating Systems & Processes', 'Video', 'https://www.youtube.com/watch?v=26QPDBe-NB8', 'Engaging video overview explaining multiprogramming, context switching, CPU virtualization, and process isolation.', 'Beginner'),
(58, 23, 'OSTEP: Address Translation, Paging, and Virtual Memory', 'Documentation', 'https://pages.cs.wisc.edu/~remzi/OSTEP/vm-paging.pdf', 'Authoritative textbook chapter detailing virtual addresses, page frames, page table entries, TLBs, and multi-level page tables.', 'Advanced'),
(59, 23, 'Virtual Memory, Page Replacement, and Thrashing Explained', 'Article', 'https://www.geeksforgeeks.org/virtual-memory-in-operating-system/', 'Detailed tutorial on demand paging, page fault handling sequences, FIFO, LRU, and Optimal page replacement algorithms.', 'Advanced'),
(60, 23, 'Operating Systems Memory Management Practice Questions', 'Practice', 'https://www.sanfoundry.com/operating-system-questions-answers-virtual-memory/', 'Multiple-choice questions and problem-solving exercises on effective memory access time, TLB hit ratio, and page table sizing.', 'Advanced'),
(61, 23, 'Crash Course Computer Science: Memory & Storage Systems', 'Video', 'https://www.youtube.com/watch?v=p3q5zWCw8J4', 'Illustrated video lecture explaining RAM, cache hierarchies, virtual memory paging, and swapping mechanics.', 'Beginner'),
(62, 7, 'Python Official Documentation: Data Structures (Lists, Tuples, Sets)', 'Documentation', 'https://docs.python.org/3/tutorial/datastructures.html', 'Official Python tutorial covering list methods, list comprehensions, immutable tuples, tuple packing/unpacking, and set algebra.', 'Beginner'),
(63, 7, 'Real Python: Python Lists and Tuples — Concepts and Practical Guide', 'Article', 'https://realpython.com/python-lists-tuples/', 'Comprehensive article explaining memory allocation differences, immutability guarantees, indexing, and slice assignments.', 'Beginner'),
(64, 7, 'W3Schools Interactive Python Collections Practice', 'Practice', 'https://www.w3schools.com/python/python_lists.asp', 'Interactive code challenges and quizzes for practicing list manipulation, tuple immutability, and set membership testing.', 'Beginner'),
(65, 7, 'freeCodeCamp: Python Lists, Tuples, and Sets Tutorial', 'Video', 'https://www.youtube.com/watch?v=rfscVS0vtbw', 'Video lecture section demonstrating creating, mutating, iterating, and filtering Python lists, tuples, and mathematical sets.', 'Beginner'),
(66, 8, 'Python Official Documentation: Mapping Types — dict', 'Documentation', 'https://docs.python.org/3/library/stdtypes.html#mapping-types-dict', 'Standard library reference on dictionary keys, values, items, get with default, dictionary comprehensions, and dict merging.', 'Intermediate'),
(67, 8, 'Real Python: Dictionaries in Python — The Complete Guide', 'Article', 'https://realpython.com/python-dicts/', 'In-depth exploration of hash table mechanics, hashability, collision resolution, key restrictions, and performance benchmarks.', 'Intermediate'),
(68, 8, 'LeetCode Explore: Hash Table Data Structure Practice', 'Practice', 'https://leetcode.com/explore/learn/card/hash-table/', 'Hands-on problem sets implementing key-value maps, duplicate detection, anagram grouping, and frequency counters.', 'Intermediate'),
(69, 8, 'Python Dictionary Methods and Time Complexities Notes', 'Notes', 'https://www.geeksforgeeks.org/python-dictionary/', 'Concise reference notes summarizing Big-O time complexity for insertion, lookup, and deletion across standard Python dicts.', 'Intermediate'),
(70, 11, 'MDN Web Docs: JavaScript First Steps', 'Documentation', 'https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps', 'Foundational Mozilla guide covering variables (let, const), basic arithmetic, string manipulation, conditionals, and functions.', 'Beginner'),
(71, 11, 'The Modern JavaScript Tutorial: Fundamentals & Data Types', 'Article', 'https://javascript.info/first-steps', 'Deep conceptual tutorial covering dynamic typing, type conversions, truthy/falsy expressions, and modern arrow functions.', 'Intermediate'),
(72, 11, 'FreeCodeCamp: Basic JavaScript Interactive Coding Curriculum', 'Practice', 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/#basic-javascript', 'Browser-based coding challenges testing fundamentals including arrays, objects, loops, functions, and scopes.', 'Intermediate'),
(73, 11, 'freeCodeCamp: JavaScript Programming Full Course for Beginners', 'Video', 'https://www.youtube.com/watch?v=W6NZfCO5SIk', 'Comprehensive beginner video tutorial introducing JavaScript variables, conditional branching, functions, and DOM basics.', 'Beginner');
