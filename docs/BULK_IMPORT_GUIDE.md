# TezMindz Bulk Excel Import System - Mentor & Content Team Guide

Welcome to the **TezMindz Bulk Import System**. This tool allows mentors, educators, and administrators to upload large volumes of curriculum data, Question banks (e.g. 500+ Olympiad and Mock Test questions), Game content, and Quizzes into the TezMindz platform in seconds using Microsoft Excel (`.xlsx`).

---

## 🌟 Key Principles

1. **Same Models as Manual Entry**: Whether you add a Question manually in Django Admin or import 500 questions from an Excel sheet, they live in the **exact same database models**, follow the **exact same validation rules**, and immediately appear in the student platform.
2. **Safe & Atomic**: If an Excel sheet has 500 rows and even 1 row has an error, the system will **never** leave half-imported, corrupt data. Everything is inspected in a **Validation Preview** first.
3. **No Coding Required**: Downloadable templates with dropdowns and clear guidance rows make spreadsheet preparation straightforward.

---

## 🚀 How to Perform an Import

### Step 1: Navigate to Bulk Import Hub
1. Log in to the TezMindz Admin at `/admin/`.
2. On the left sidebar or on the top dashboard shortcut buttons, click **Bulk Import Hub** (or go to `/admin/bulk-import/`).

### Step 2: Download the Template
1. Choose the category you want to import:
   - **Curriculum**: Grades, Learning Worlds (Subjects), Chapters, and Concepts.
   - **Question Bank & Mock Tests**: Practice questions, choices, answers, marks, and explanations.
   - **Game Content**: Level challenges and interactive steps for Game Plugins.
   - **Quizzes & Mock Tests**: Full timed tests with mapped questions.
2. Click **Template** to download the official `.xlsx` template.

### Step 3: Fill Out Your Data in Excel
- Follow the column headers provided in Row 1.
- Read the instructions in Row 2.
- Fill in your rows starting from Row 3.
- Save your workbook as standard `.xlsx`.

### Step 4: Upload Your Spreadsheet
1. Click **Upload** on the chosen category card.
2. Drag & drop your `.xlsx` file into the upload zone (or click to browse).
3. Click **Upload & Validate Spreadsheet**.

### Step 5: Review the Validation Preview
The system will parse all rows and present an interactive summary:
- **Total Rows**: Count of rows analyzed.
- **Valid Rows**: Records that successfully matched the curriculum and passed formatting rules.
- **Errors**: Number of problems detected.
- **New Creates / Updates / Duplicates**: Breakdown of actions that will be performed.

### Step 6: Resolving Errors (If Any)
- If errors exist, the **Confirm Import** button is disabled to protect your database.
- Click **Download Error Report (.xlsx)** to download a spreadsheet with row numbers and specific explanations (e.g., *Row 45: Concept 'Addition' belongs to Chapter 'Numbers', not 'Fractions'*).
- Fix the cells in your Excel file and upload again.

### Step 7: Confirm & Import
- Once all errors are 0, click the green **Confirm & Import Now** button.
- The transaction commits atomically.
- You can immediately click **View Imported Records in Admin** to view and edit individual records.

---

## 📋 Supported Import Categories & Columns

### 1. Curriculum Import
| Column Header | Required? | Allowed Values / Examples | Description |
|---|---|---|---|
| **Grade** | **Yes** | `Class 1` to `Class 12`, `Grade 5`, or integer `5` | The class / standard level. Must match existing Grade. |
| **Subject** | **Yes** | `Mathematics`, `Science`, `English` | Learning World / Subject name. |
| **Chapter** | **Yes** | e.g. `Number & Operations`, `Fractions` | Chapter (Topic) title. |
| **Concept** | **Yes** | e.g. `Place Value Systems` | Concept / mission title. |
| **Chapter Order** | No | `1`, `2`, `3` | Display sequence for the chapter. |
| **Chapter Difficulty** | No | `easy`, `medium`, `hard` | Difficulty tag (default: `easy`). |
| **Chapter Description** | No | Any text | Overview of the chapter. |
| **Concept Order** | No | `1`, `2`, `3` | Display sequence for concept within chapter. |
| **Concept Content** | No | Markdown or plain text | Explanatory learning note shown to students. |

---

### 2. Question Bank & Mock Test Import
Used for importing hundreds of Olympiad and Mock Test questions per grade.

| Column Header | Required? | Allowed Values / Examples | Description |
|---|---|---|---|
| **Grade** | **Yes** | `Class 5`, `Grade 5`, or `5` | Academic class level. |
| **Subject** | **Yes** | `Mathematics`, `Science`, etc. | Subject name. |
| **Chapter** | **Yes** | e.g. `Number & Operations` | Chapter the question belongs to. |
| **Concept** | No | e.g. `Place Value Systems` | Specific concept. If provided, must belong to the chapter. |
| **Question Prompt** | **Yes** | Any question text or problem statement | The question text displayed to the student. |
| **Option A** | **Yes** | Text or numbers (e.g. `90,000`) | First choice option. |
| **Option B** | **Yes** | Text or numbers (e.g. `9,000`) | Second choice option. |
| **Option C** | No | Text or numbers (e.g. `900`) | Third choice option. |
| **Option D** | No | Text or numbers (e.g. `90`) | Fourth choice option. |
| **Correct Answer** | **Yes** | `A`, `B`, `C`, `D` or the exact option text | The correct answer key. |
| **Difficulty** | No | `easy`, `medium`, `hard` | Difficulty level (default: `easy`). |
| **Marks** | No | Positive integer (e.g. `1`, `2`, `4`) | Points awarded for correct answer (default: `1`). |
| **Negative Marks** | No | Positive integer (e.g. `0`, `1`) | Penalty for incorrect answer (default: `0`). |
| **Explanation** | No | Text | Explanation shown to the student after completing the quiz. |
| **Allow Multiple Answers** | No | `TRUE` or `FALSE` | Set `TRUE` if question has multiple correct options (default: `FALSE`). |
| **Hint 1** | No | Helpful text for student | In-game hint text. |
| **Question ID** | No | Existing numeric ID (e.g. `1042`) | Leave **blank** to create a new question. Provide an existing ID to **update** that question. |

---

### 3. Game Content Import
Supplies interactive challenge parameters and steps to frontend Game Plugins.

| Column Header | Required? | Allowed Values / Examples | Description |
|---|---|---|---|
| **Game Title** | **Yes** | e.g. `Dream House Builder 3D` | Exact title of the existing Game in Game Library. |
| **Step Order** | **Yes** | `1`, `2`, `3` | Step sequence within the game. |
| **Prompt** | **Yes** | Challenge text (e.g. `Solve 45 x 6`) | Challenge objective or question shown in game. |
| **Content Type** | No | `standard`, `read_number`, `fraction_slice` | Mechanic type for the game plugin. |
| **Points** | No | e.g. `10`, `15` | XP/points earned upon completing this step. |
| **Target Data (JSON)** | No | `{"target": 270}` | Target parameters for Canvas/3D engine. |
| **Correct Answer (JSON)** | No | `"270"` or `{"num": 3, "den": 4}` | Verification rule. |
| **Hints (JSON)** | No | `["Multiply 40x6 then 5x6"]` | Hint array for the step. |

---

### 4. Quizzes & Mock Tests Import
Builds timed mock tests and automatically attaches the question bank items to them.

| Column Header | Required? | Allowed Values / Examples | Description |
|---|---|---|---|
| **Quiz Title** | **Yes** | e.g. `All-India Math Olympiad Mock 1` | Name of the Mock Test or Quiz. |
| **Grade** | **Yes** | e.g. `Class 5` | Class level. |
| **Subject** | **Yes** | e.g. `Mathematics` | Subject name. |
| **Chapter** | **Yes** | e.g. `Number & Operations` | Chapter tested. |
| **Quiz Duration (Mins)** | No | e.g. `20`, `45`, `60` | Timed test duration in minutes (leave blank for untimed). |
| **Question Prompt** | **Yes** | Question text | Question prompt. |
| **Option A, B, C, D** | **Yes** | Options text | Choices for the question. |
| **Correct Answer** | **Yes** | `A`, `B`, `C`, `D` | Correct option letter. |

---

## 🔍 How Relationship Validation Works

The TezMindz hierarchy enforces strict educational relationships:

```
Grade (e.g. Class 5)
  └── Subject / Learning World (e.g. Mathematics)
        └── Chapter / Topic (e.g. Fractions & Decimals)
              └── Concept (e.g. Pizza Fraction Challenge)
                    └── Question / Game Content / Quiz
```

1. **Chapter Parentage**: If you specify `Grade: Class 5`, `Subject: Science`, and `Chapter: Fractions & Decimals`, the importer detects that `Fractions & Decimals` belongs to *Mathematics*, not *Science*, and flags an error with the exact row number.
2. **Concept Parentage**: If you specify a Concept, it must belong to the specified Chapter. It cannot be reassigned to an unrelated chapter.
3. **Correct Answer Verification**: The importer validates that the correct answer matches one of the provided options. If you enter `C`, Option C must be filled in.

---

## ✏️ Editing Imported Data Afterward

All imported records are regular Django models:
- **Questions**: Go to `/admin/assessments/question/`. Filter by Subject, Difficulty, or search by text. You can edit options, marks, or hints individually.
- **Quizzes**: Go to `/admin/assessments/quiz/`. Adjust duration, question order, or publish status.
- **Chapters & Concepts**: Go to `/admin/curriculum/topic/` and `/admin/curriculum/concept/`.
- **Game Content**: Go to `/admin/games/game/` and scroll down to the **Game Content / Question** inline table.

---

## 🔒 Security & Audit Logging
- Only staff and admin users can perform bulk imports.
- Every import session is permanently recorded in the **Bulk Import Audit Log** (`/admin/bulk_import/bulkimportjob/`).
- The log records who uploaded the file, filename, timestamp, row counts, and summary messages for full accountability.
