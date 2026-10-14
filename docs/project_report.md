# Project Report - AI Student Learning Mentor

**Project Title:** AI Student Learning Mentor  
**Academic Degree:** Bachelor of Technology (B.Tech) in Computer Science & Engineering  
**Department:** Department of Computer Science & Engineering  
**Institution:** Institute of Technical Education & Research (ITER), Siksha 'O' Anusandhan (Deemed to be University)  
**Author:** Subham Kumar Dash  
**Registration Number:** 2241019445  
**Submission Scope:** Technical Project Documentation & System Verification  
**UN Sustainable Development Goal:** **SDG 4 - Quality Education** (Targets 4.4 and 4.7)  

---

## Abstract

Self-directed computer science education is routinely hindered by curriculum fragmentation, rigid study calendars, disconnect between conceptual reading and assessment, and prohibitive costs of 1-on-1 academic tutoring. Furthermore, existing commercial educational portals often substitute real academic evaluation with synthetic vanity metrics.

**AI Student Learning Mentor** addresses these challenges by delivering an authentic, secure, full-stack web application designed to guide university students through structured academic roadmaps. Built on **Python 3.10+ / Flask 3.1.3** and backed by a relational **MySQL** database, the system provides:
1. **Deterministic Personalized Study Planning:** Mathematically paces curriculum topics into day-by-day task schedules based on student skill level (Beginner, Intermediate, Advanced) and duration (1-60 days).
2. **Cheat-Resistant Practice Quizzes:** Evaluates conceptual comprehension using server-side grading, instant reviews, and performance tier analysis.
3. **Context-Aware AI Doubt Mentorship:** Delivers step-by-step academic explanations grounded in syllabus topics via Google Gemini / OpenAI with rate-limiting controls.
4. **Evidence-Based Progress Tracking:** Computes honest topic mastery percentages strictly from verified quiz attempts and completed study milestones - with zero simulated or synthetic data.
5. **Data-Driven Personalized Recommendations:** Identifies weak topics and schedules reinforcement quizzes.

The system is fully hardened against OWASP Top 10 vulnerabilities (including CSRF, IDOR, SQL injection, and XSS) and verified with **201 automated regression tests** and comprehensive **Google Chrome browser automation** across Desktop, Tablet, and Mobile viewports.

---

## 1. Introduction & Problem Statement

### 1.1 Background & Motivation
In modern undergraduate engineering education, self-paced learning is vital. However, students navigating complex topics such as *Data Structures & Algorithms*, *Database Management Systems*, *Operating Systems*, and *Computer Networks* often struggle to identify high-quality learning resources, track their genuine syllabus coverage, and resolve doubts when instructors are unavailable.

### 1.2 Problem Statement
1. **Curriculum Fragmentation:** High-quality documentation, textbooks, articles, and code exercises are scattered across hundreds of disparate websites without clear syllabus organization.
2. **One-Size-Fits-All Scheduling:** Standard course calendars do not adjust to varying temporal constraints or prior student knowledge.
3. **Assessment Disconnect:** Reading static notes without immediate practice fails to build problem-solving retention.
4. **Inaccessible Tutoring:** Personalized academic mentorship remains financially out of reach for a majority of students worldwide.
5. **Vanity Progress Dashboards:** Many learning platforms display arbitrary progress meters based merely on clicks or time spent, misleading students about their exam readiness.

### 1.3 UN SDG 4 Alignment
The platform directly supports **United Nations Sustainable Development Goal 4 (Quality Education)**:
- **Target 4.4:** Enhancing technical competencies in programming, algorithms, databases, and systems.
- **Target 4.7:** Providing open educational resources and verifiable learning milestones.
- **Equity in Mentorship:** Eliminating socioeconomic barriers by providing free, high-quality, 24/7 academic guidance.

---

## 2. System Architecture & Modular Design

The application follows a clean 4-tier **Modular MVC with Service & Data Layer** architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                              │
│   Jinja2 Templates (templates/) + Modular CSS (static/css/) + ES6 JS   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / HTML / JSON
┌───────────────────────────────────▼────────────────────────────────────┐
│                         ROUTING LAYER (Flask)                          │
│   8 Modular Blueprints (auth, dashboard, profile, study_plan, etc.)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Python Service Calls
┌───────────────────────────────────▼────────────────────────────────────┐
│                         SERVICE LAYER (Business Logic)                 │
│   auth_service, study_plan_service, quiz_service, ai_service, etc.     │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
┌──────────────────▼─────────────┐ ┌─────────────────▼───────────────────┐
│       MODELS & DATA LAYER      │ │         AI PROVIDER ENGINE          │
│   Repository / Active Record   │ │   Google Gemini REST API / OpenAI   │
│   db_connection (PyMySQL Pool) │ │   Rate-Limiter & Safe Fallback      │
└──────────────────┬─────────────┘ └─────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────────────────────┐
│                 RELATIONAL DATABASE PERSISTENCE                        │
│                   MySQL / MariaDB (`edumentor_ai`)                     │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Layer Breakdown
1. **Presentation Layer:** Jinja2 templates organized by feature domain (`auth/`, `dashboard/`, `profile/`, `study_plan/`, `resources/`, `quiz/`, `progress/`, `ai_assistant/`) with responsive modular CSS (`style.css`, `auth.css`, `dashboard.css`, `study_plan.css`, `quiz.css`, `chat.css`).
2. **Routing Layer (`routes/`):** 8 Flask Blueprints with centralized URL rule registration maintaining exactly 51 endpoints.
3. **Service Layer (`services/`):** Encapsulates business logic, including study plan allocation algorithms, cheat-resistant quiz evaluation, progress score weighting, and personalized recommendation generation.
4. **Data Models Layer (`models/`):** 6 domain model modules managing SQL queries, parameterization, and database entity mapping.
5. **Database Backend:** Relational MySQL schema with strict foreign keys and cascading referential integrity.

---

## 3. Database Schema Design

The `edumentor_ai` schema consists of **10 interconnected relational tables**:

| Table | Primary Key | Foreign Keys | Purpose |
| :--- | :--- | :--- | :--- |
| `users` | `id` (INT) | None | Authenticated student accounts and role attributes |
| `student_profiles` | `id` (INT) | `user_id` → `users.id` | Academic degree, semester, skill level, and goals |
| `subjects` | `id` (INT) | None | Core academic disciplines (e.g. Python, DBMS, OS) |
| `topics` | `id` (INT) | `subject_id` → `subjects.id` | Granular curriculum syllabus topics |
| `resources` | `id` (INT) | `topic_id` → `topics.id` | Verified documentation, notes, and exercises |
| `study_plans` | `id` (INT) | `user_id`, `subject_id` | Student study plan instances (1-60 days duration) |
| `study_plan_items` | `id` (INT) | `plan_id`, `topic_id` | Day-by-day scheduled learning tasks and checkboxes |
| `quizzes` | `id` (INT) | `topic_id` → `topics.id` | Conceptual MCQs with 4 options and difficulty ratings |
| `quiz_attempts` | `id` (INT) | `user_id`, `topic_id` | Authenticated attempt records with calculated scores |
| `quiz_attempt_answers`| `id` (INT) | `attempt_id`, `question_id` | Granular per-question submitted vs correct answers |

All user-dependent tables implement `ON DELETE CASCADE` to ensure strict referential integrity.

---

## 4. Key Functional Modules

### 4.1 Authentication & Profile Management
- Secure user registration and sign-in backed by Werkzeug's cryptographic `scrypt` hashing algorithm.
- Session management with strict cookie security (`HttpOnly`, `SameSite=Lax`).
- Student profile customization tracking degree course, semester, preferred daily study time, and primary learning goal with automated profile completion percentage.

### 4.2 Curriculum & Verified Resources
- Hierarchical catalog spanning 7 core disciplines (*Python Programming*, *Data Structures & Algorithms*, *Web Development*, *Java Programming*, *Database Management Systems*, *Computer Networks*, *Operating Systems*) and 23 syllabus topics.
- Curated multi-format learning resources (Official Documentation, In-Depth Articles, Comprehensive Notes, Interactive Practice Challenges) with validated external URLs.

### 4.3 Deterministic Study Plan Generator
- Custom scheduling engine capable of generating 1-day crash reviews up to 60-day deep dives.
- Allocates topics based on student skill tier:
  - *Beginner:* 1 topic per day with repetition and fundamental pacing.
  - *Intermediate:* Balanced multi-topic allocation.
  - *Advanced:* Accelerated progression with concurrent practice milestones.
- Interactive task completion checklists with real-time progress recalculation.

### 4.4 Quiz & Practice Engine
- 115 conceptual practice questions across all 23 curriculum topics.
- **Cheat-Resistant Security:** Question options (A, B, C, D) are served to the client without `correct_answer`. Scoring is computed server-side only upon POST submission.
- Instant score breakdown with performance tiers (*Mastery*, *Proficient*, *Needs Revision*) and answer reviews.

### 4.5 Context-Aware AI Doubt Assistant
- Integrates with Google Gemini REST API (or OpenAI) to provide academic conceptual explanations.
- Prompts are automatically infused with the student's selected subject and topic context.
- Includes rate-limiting controls, client-side live character counting (2000 character maximum), and offline graceful fallbacks.

### 4.6 Evidence-Based Progress Tracking
- Topic mastery is computed deterministically:
  $$\text{Mastery Percentage} = 0.4 \times (\text{Task Completion Rate}) + 0.6 \times (\text{Average Quiz Accuracy})$$
- Progress Center presents overall mastery meters, subject cards, weak topic revision alerts, and chronological learning activity logs.

### 4.7 Recommendation Service
- Cross-references student quiz history and pending study plan tasks to identify weak topics (average score $< 60\%$) and next syllabus milestones.
- Formats actionable study recommendations linking directly to verified `/topics/<id>` study guides.

---

## 5. Security & Privacy Architecture

The platform incorporates comprehensive application-level security controls:

1. **CSRF Protection:** Cryptographic session-backed tokens generated per user session and validated on every state-changing `POST` request.
2. **Tenant Isolation & IDOR Defense:** Access to study plans, quiz results, and chat histories is strictly scoped to the authenticated `session['user_id']`. Accessing other students' records returns HTTP 404.
3. **SQL Injection Defense:** 100% of database interactions utilize PyMySQL parameterized placeholders (`%s`); zero string formatting in SQL queries.
4. **XSS Defense:** Jinja2 autoescaping enabled globally across all template views.
5. **Open Redirect Defense:** URL redirection parameters (`next`) are strictly validated against `url_has_allowed_host_and_scheme`.
6. **API Key & Secret Isolation:** AI keys and database credentials reside strictly in server `.env` files; never exposed to client-side assets.

---

## 6. Verification, Testing & Quality Assurance

### 6.1 Automated Test Suite
The project includes a 10-module test suite executing **201 automated tests**:

| Test Module | Coverage Area | Test Count | Result |
| :--- | :--- | :-: | :---: |
| `tests/test_foundation.py` | Database connectivity, schema tables, password hashing | 17 | **PASS** ✅ |
| `tests/test_auth_profile.py` | Registration, login, profile updates, session management | 24 | **PASS** ✅ |
| `tests/test_learning_content.py`| Subjects catalog, topic detail, resource links, search | 18 | **PASS** ✅ |
| `tests/test_study_plans.py` | Study plan creation, item pacing, task toggling | 21 | **PASS** ✅ |
| `tests/test_quizzes.py` | Catalog, briefing, cheat-resistance, grading, history | 30 | **PASS** ✅ |
| `tests/test_ai_assistant.py` | AI assistant prompts, context injection, rate limiting | 18 | **PASS** ✅ |
| `tests/test_progress.py` | Weighted progress formulas, weak topics, activity feed | 16 | **PASS** ✅ |
| `tests/test_recommendations.py`| Weak topic recommendations, next steps, goal lookup | 14 | **PASS** ✅ |
| `tests/test_security_hardening.py` | CSRF enforcement, IDOR isolation, open redirect guard | 25 | **PASS** ✅ |
| `tests/test_system_integration.py` | End-to-end integration flows, health check endpoint | 18 | **PASS** ✅ |
| **Total Test Suite** | **Full Application System Test** | **201** | **100% PASS** ✅ |

Execution command:
```bash
python -m unittest discover -s tests -p "test_*.py"
Ran 201 tests in 37.411s - OK
```

### 6.2 Browser-Level Visual & Responsive Verification
All 20 application pages were rendered and audited in **Google Chrome 154.0.8037.99 (Official Build) (64-bit)** using Chrome DevTools Protocol (CDP) across three viewport standards:
- **Desktop:** `1366 × 768`
- **Tablet:** `768 × 1024`
- **Mobile:** `390 × 844`

**Audit Results:**
- **60 full-page screenshots captured** and archived in [`docs/screenshots/phase_5_1/`](file:///C:/AI-Student-Learning-Mentor/docs/screenshots/phase_5_1/).
- **0 horizontal overflows** detected (`scrollWidth <= innerWidth` across all 60 viewports).
- **0 broken images** detected (`img.naturalWidth > 0`).
- **0 uncaught JavaScript runtime exceptions** in browser console.
- **9 out of 9 interactive functional smoke tests passed** (form validation, CSRF handling, task checkbox toggles, quiz options, live character counters, topic routing, logout session teardown, and custom 404/500 error templates).

---

## 7. Screenshot Gallery & Interface Overview

The project documentation repository contains full visual evidence of the operating interface:

| View Description | Baseline Screenshot | Responsive Capture |
| :--- | :--- | :--- |
| **Public Landing Page** | `docs/screenshots/01_home_page.png` | `docs/screenshots/phase_5_1/01_landing_page_desktop.png` |
| **Sign In Page** | `docs/screenshots/03_login_page.png` | `docs/screenshots/phase_5_1/02_login_page_desktop.png` |
| **Registration Page** | `docs/screenshots/04_register_page.png` | `docs/screenshots/phase_5_1/03_register_page_desktop.png` |
| **Subjects Catalog** | `docs/screenshots/02_subjects_catalog.png`| `docs/screenshots/phase_5_1/04_subjects_catalog_desktop.png`|
| **Subject Detail Page** | `docs/screenshots/06_subject_detail.png` | `docs/screenshots/phase_5_1/05_subject_detail_desktop.png` |
| **Topic Detail Page** | `docs/screenshots/07_topic_detail.png` | `docs/screenshots/phase_5_1/06_topic_detail_desktop.png` |
| **Student Dashboard** | - | `docs/screenshots/phase_5_1/11_dashboard_desktop.png` |
| **Student Profile** | - | `docs/screenshots/phase_5_1/12_profile_desktop.png` |
| **Study Plans List** | - | `docs/screenshots/phase_5_1/13_study_plans_list_desktop.png` |
| **Study Plan Detail** | - | `docs/screenshots/phase_5_1/14_study_plan_detail_desktop.png` |
| **Create Study Plan** | - | `docs/screenshots/phase_5_1/15_study_plan_create_desktop.png` |
| **Quizzes Catalog** | - | `docs/screenshots/phase_5_1/07_quizzes_catalog_desktop.png` |
| **Quiz Briefing Page** | - | `docs/screenshots/phase_5_1/08_quiz_briefing_desktop.png` |
| **Quiz Taking Interface** | - | `docs/screenshots/phase_5_1/09_quiz_taking_desktop.png` |
| **Quiz Scorecard** | - | `docs/screenshots/phase_5_1/10_quiz_result_desktop.png` |
| **Progress Center** | - | `docs/screenshots/phase_5_1/16_progress_center_desktop.png` |
| **AI Doubt Assistant** | - | `docs/screenshots/phase_5_1/17_ai_chat_desktop.png` |
| **AI Chat History** | - | `docs/screenshots/phase_5_1/18_ai_history_desktop.png` |
| **Branded 404 Error Page** | `docs/screenshots/05_error_404.png` | `docs/screenshots/phase_5_1/19_error_404_desktop.png` |
| **Branded 500 Error Page** | - | `docs/screenshots/phase_5_1/20_error_500_desktop.png` |

---

## 8. Known Limitations & Future Scope

### 8.1 Current Limitations
- External AI query latency is subject to third-party API availability and quotas.
- Practice quizzes currently focus on multiple-choice conceptual questions rather than live code execution sandboxes.
- Real-time collaborative peer study groups are not yet implemented.

### 8.2 Future Scope
1. **Interactive Code Sandboxes:** Browser-based WebAssembly/Pyodide execution environments for real-time code challenge evaluation.
2. **Spaced Repetition Flashcards:** SuperMemo (SM-2) algorithm integration for long-term memory retention of syntax and conceptual definitions.
3. **Voice AI Tutoring:** Low-latency bidirectional voice conversations via Gemini Live API for spoken conceptual explanations.
4. **Learning Management System (LMS) Integration:** LTI (Learning Tools Interoperability) protocol support for institutional Canvas, Moodle, and Blackboard deployments.

---

## 9. Conclusion

The **AI Student Learning Mentor** demonstrates that a modern, accessible, and pedagogically sound educational platform can be constructed through disciplined full-stack engineering. By combining deterministic scheduling, cheat-resistant assessment, evidence-based progress calculation, and syllabus-grounded AI tutoring, the platform provides computer science students with a reliable companion for academic success.

The project fulfills all requirements for undergraduate technical evaluation, with complete test suite coverage, real-browser visual responsiveness, and rigorous application security.
