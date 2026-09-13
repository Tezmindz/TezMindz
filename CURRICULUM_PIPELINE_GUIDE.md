# TezMindz Curriculum & Game Engine Pipeline Architecture

This document details how curriculum content is structured, authored in Admin, delivered to the student web interface, and integrated with game engines and quizzes.

---

## 1. Authoritative Student Content Hierarchy

The student learning pipeline follows a strictly data-driven hierarchy:

```
Grade (e.g. Class 5)
  ↓
Subject / Learning World (e.g. Mathematics, Science, English)
  ↓
Chapter (Django Model: Topic)
  ↓
Concept (Django Model: Concept)
  ↓
Game / Quiz (Django Models: Game, Quiz)
  ↓
Game Session / Quiz Attempt (GameSession, QuizAttempt)
  ↓
XP / Coins / TopicProgress (StudentProfile, TopicProgress, XPTransaction)
```

> **Note on Naming:** Internal Django models use `Topic` to represent chapters for historical compatibility, but all user-facing UI, URLs, and labels authoritative denote them as **Chapter**.

---

## 2. Admin Authoring Workflow

1. **Grade Creation:**
   - Admin creates `Grade` (e.g. Name: `"5"`, Order: `5`).
2. **Subject Creation:**
   - Admin creates `Subject` (e.g. Name: `"Mathematics"`, Slug: `"mathematics"`, Order: `1`).
3. **Chapter (Topic) Creation:**
   - Admin creates `Topic` linking to `Subject` and `Grade` with status `published`.
4. **Concept Creation:**
   - Admin creates `Concept` linking to `Topic` with status `published` and pedagogical descriptions.
5. **Game Configuration:**
   - Admin creates `Game` linking to `Concept` with status `published`, game type (`house_builder`, `math_challenge`, etc.), and JSON `config`.
6. **Quiz & Question Configuration:**
   - Admin creates `Quiz` linked to `Topic`, creates `Question` items linked to `Concept`/`Topic`, and links them via `QuizQuestion` order.

---

## 3. Student Delivery & Navigation Routes

- `/dashboard/`: Authoritative learning world overview dynamically filtered by `student_profile.grade`.
- `/learn/`: Subject catalog and curriculum track.
- `/subject/<id>/`: Chapter listing for the subject and student grade, displaying progress %, concept counts, and completion status.
- `/chapter/<id>/`: Concept missions listing for the chapter with dynamic progress indicators.
- `/concept/<id>/`: Mission hub for the concept containing:
  - Step 1: Interactive Learning Theater & AI Teacher Companion.
  - Step 2: Educational Game Challenge (`/game/<game_id>/play/`).
  - Step 3: Chapter Mastery Quiz (`/quiz/<quiz_id>/`).
- `/games/`: Interactive Game Arena listing all published games matching the student's grade.

---

## 4. Game Integration Contract for Game Developers

Game developers integrating new games do **NOT** need to edit Django view or template code to register a game.

### Canonical Game Launch URL
```
GET /game/<game_id>/play/
```
This renders the standalone responsive game frame configured with the game's dynamic metadata, pass-through tokens, and session hooks.

### Generic Game Submission APIs

#### Option A: Direct Client Submission (Stateless)
Ideal for client-side HTML5/Canvas/WebGL games that calculate final score locally:
```http
POST /api/game/submit/
Content-Type: application/json
Authorization: Bearer <JWT_ACCESS_TOKEN>  (or authenticated session cookie)

{
  "game_id": 12,
  "score": 85,
  "accuracy": 90,
  "time_taken_seconds": 45
}
```
**Response:**
```json
{
  "success": true,
  "session_id": "uuid-or-id",
  "score": 85,
  "accuracy": 90.0,
  "xp_awarded": 15,
  "coins_awarded": 7,
  "total_xp": 175
}
```

#### Option B: Stateful Game Session (Secure Server-Validated Levels)
1. **Start Session:**
   ```http
   POST /api/game/<game_id>/start/
   Authorization: Bearer <JWT_ACCESS_TOKEN>
   ```
   *Response includes `session_id` and game `config` JSON.*

2. **Submit Move/Level:**
   ```http
   POST /api/game/sessions/<session_id>/submit/
   Content-Type: application/json
   Authorization: Bearer <JWT_ACCESS_TOKEN>

   {
     "level_id": 1,
     "answer": "180deg",
     "time_taken": 12,
     "is_correct": true
   }
   ```
   *Response verifies move against `game.config` and disburses level XP/coins.*

---

## 5. Automated Verification & Isolation

All pipeline relationships are verified using isolated automated test suites:
- `python test_e2e_pipeline.py`: Validates end-to-end admin curriculum creation through student navigation, game launch, game submission, quiz submission, and wallet rewards.
- Model properties (`title`, `chapter`, `question_text`, `option_text`) guarantee backward and forward compatibility between Django templates and API serializers.
