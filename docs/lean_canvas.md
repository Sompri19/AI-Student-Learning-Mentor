# Lean Canvas - AI Student Learning Mentor

**Project Title:** AI Student Learning Mentor  
**Academic Submission:** B.Tech Final Project Evaluation  
**Author:** Subham Kumar Dash (Reg. No: 2241019445)  
**Institution:** Department of Computer Science & Engineering, ITER, Siksha 'O' Anusandhan (Deemed to be University)  
**UN SDG Alignment:** SDG 4 - Quality Education (Targets 4.4 & 4.7)  

---

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ 1. PROBLEM                      │ 4. SOLUTION                     │ 3. UNIQUE VALUE PROPOSITION     │ 9. UNFAIR ADVANTAGE             │ 2. CUSTOMER SEGMENTS            │
│                                 │                                 │                                 │                                 │                                 │
│ Top 3 Problems:                 │ Top 5 Features:                 │ Single Clear Message:           │ Defensible Edge:                │ Target Users:                   │
│ 1. Curriculum Fragmentation:    │ 1. Granular Curriculum Mapping: │ "A unified, data-driven         │ 1. Genuine Evidence-Based       │ 1. Undergraduate CS & IT        │
│    Educational resources (docs, │    7 CS subjects & 23 topics    │    academic mentorship platform │    Mastery: Zero synthetic      │    students preparing for       │
│    notes, videos, practice) are │    with curated notes, docs,    │    combining deterministic      │    vanity metrics; mastery is   │    semester exams and technical │
│    scattered across disparate   │    and practice exercises.      │    study plans, cheat-resistant │    strictly computed from       │    recruitment interviews.      │
│    platforms with no mapping to │ 2. Deterministic Study Planner: │    practice quizzes, evidence-  │    authenticated quiz attempts  │ 2. Self-Taught Programmers &    │
│    specific syllabus topics.    │    Mathematical day-by-day      │    based progress tracking, and │    and completed study tasks.   │    Career Switchers needing     │
│ 2. Rigid, Generic Schedules:    │    schedules (1-60 days)        │    syllabus-grounded AI doubt   │ 2. Deep Curriculum Cohesion:    │    structured academic syllabus │
│    Standard course calendars fail│   adapted to student skill tier │   tutoring."                    │    Every study milestone, quiz  │    guidance.                    │
│    to adapt to individual skill │    (Beginner, Int, Adv).        │                                 │    question, and AI prompt is   │ 3. High School & Vocational     │
│    levels and temporal needs.   │ 3. Practice Quiz Engine:        │ High-Level Concept:             │    firmly mapped to relational  │    students building foundational│
│ 3. Assessment & Tutoring Gap:   │    115 conceptual MCQs with     │ "Your Personal AI-Powered       │    syllabus topics.             │    programming concepts.        │
│    Practice questions lack      │    server-side scoring, instant │  Learning Companion"            │ 3. Resilient Multi-Provider AI: │                                 │
│    instant conceptual feedback; │    review, and score tiers.     │                                 │    Architected with Gemini/     │ Early Adopters:                 │
│    1-on-1 private tutoring is   │ 4. Contextual AI Doubt Mentor:  │                                 │    OpenAI support, rate-        │ Computer science students in    │
│    expensive and inaccessible.  │    Syllabus-aware assistance    │                                 │    limiting controls, and clean │ core semesters (Semesters 3-6)  │
│                                 │    with rate limiting and safe  │                                 │    offline fallback modes.      │ studying Data Structures, DBMS, │
│ Existing Alternatives:          │    offline fallback.            │                                 │ 4. Comprehensive Security:      │ OS, and Python/Java.            │
│ • Generic LLMs (unanchored chat)│ 5. Real Progress Analytics:     │                                 │    OWASP Top 10 hardened        │                                 │
│ • Disorganized YouTube playlists│    Weighted topic mastery based │                                 │    (CSRF, IDOR isolation,       │                                 │
│ • Static, inflexible PDF notes  │    on actual student evidence.  │                                 │    parameterized SQL, scrypt).  │                                 │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ 8. KEY METRICS                  │                                 │                                 │                                 │ 5. CHANNELS                     │
│                                 │                                 │                                 │                                 │                                 │
│ • User Profiles Created & Goals │                                 │                                 │                                 │ Path to Users:                  │
│ • Study Plans Generated         │                                 │                                 │                                 │ • University departmental       │
│ • Daily Tasks Checked Off       │                                 │                                 │                                 │   deployment & lab portals.     │
│ • Quizzes Attempted & Avg Score │                                 │                                 │                                 │ • GitHub open-source repository │
│ • AI Doubts Asked & Resolved    │                                 │                                 │                                 │   and developer community.      │
│ • Topic Mastery Completion Rate │                                 │                                 │                                 │ • Student hackathons, coding    │
│                                 │                                 │                                 │                                 │   clubs, and academic seminars. │
├─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┤
│ 7. COST STRUCTURE                                                 │ 6. REVENUE / SUSTAINABILITY STREAMS                                 │
│                                                                   │                                                                     │
│ • Cloud Infrastructure: Web application server (WSGI/Waitress/    │ • Student Open-Source Tier: Core curriculum, study planner, and     │
│   Gunicorn) and MySQL relational database hosting.                │   quizzes remain 100% free and open under educational mandate.      │
│ • External AI Inference: Token consumption fees for Gemini/OpenAI  │ • Institutional B2B Licensing: Tailored departmental deployments    │
│   APIs (budget-managed via per-student rate limiting).            │   with administrator analytics and LMS integration for colleges.    │
│ • Maintenance & Domain: Domain registration, SSL certificate, and │ • Premium AI Quota: Optional student upgrade tier for extended      │
│   monitoring infrastructure.                                      │   high-volume daily AI Mentor query limits.                         │
└───────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────┘
```

---

## Strategic Analysis

### 1. Problem Deep-Dive
- **Curriculum Fragmentation:** Self-directed computer science learners spend over 40% of their study time searching for appropriate study resources rather than actually studying.
- **Lack of Personalization:** A beginner and an advanced student are routinely assigned the exact same rigid 30-day syllabus by conventional educational portals.
- **Vanity Progress Tracking:** Existing e-learning dashboards display arbitrary "completion percentages" derived merely from page clicks or video watch time without testing understanding.

### 2. Solution Implementation
- **Deterministic Scheduling:** The planner calculates `ceil(topics / duration)` and distributes milestones based on pedagogical prerequisite sequences.
- **Cheat-Resistant Assessments:** Correct answers are never transmitted to the browser prior to submission. Scoring and percentage calculations are computed strictly server-side.
- **Evidence-Based Mastery:** Topic mastery is a deterministic composite of study tasks completed (40% weight) and practice quiz accuracy (60% weight).

### 3. Impact & Sustainability
By aligning directly with **UN SDG 4 (Quality Education)**, the AI Student Learning Mentor removes economic barriers to technical mentorship, delivering 24/7 personalized academic guidance to students regardless of institutional wealth.
