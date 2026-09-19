import io
from openpyxl import Workbook
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.assessments.models import Question, Option, Hint, Quiz, QuizQuestion
from apps.games.models import Game, GameContent
from apps.bulk_import.models import BulkImportJob
from apps.bulk_import.services.excel_service import ExcelService
from apps.bulk_import.services.validators import ValidatorRegistry
from apps.bulk_import.services.import_engine import ImportEngine

User = get_user_model()


class BulkImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. Admin user
        cls.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="admin_password"
        )

        # 2. Regular non-staff user
        cls.student_user = User.objects.create_user(
            username="student_test",
            email="student@test.com",
            password="student_password"
        )

        # 3. Baseline Curriculum
        cls.grade5 = Grade.objects.create(name="Class 5", order=5)
        cls.grade4 = Grade.objects.create(name="Class 4", order=4)
        cls.subject_math = Subject.objects.create(name="Mathematics", slug="mathematics", order=1)
        cls.subject_sci = Subject.objects.create(name="Science", slug="science", order=2)

        cls.topic_numbers = Topic.objects.create(
            grade=cls.grade5,
            subject=cls.subject_math,
            title="Number & Operations",
            order=1,
            status="published"
        )
        cls.topic_fractions = Topic.objects.create(
            grade=cls.grade5,
            subject=cls.subject_math,
            title="Fractions & Decimals",
            order=2,
            status="published"
        )
        cls.concept_place_value = Concept.objects.create(
            topic=cls.topic_numbers,
            title="Place Value Systems",
            content_body="Learn place value.",
            order=1,
            status="published"
        )

        # 4. Baseline Game
        cls.game_pizza = Game.objects.create(
            title="Pizza Fraction Challenge",
            concept=cls.concept_place_value,
            game_type="fraction-pizza",
            difficulty="easy",
            status="published"
        )

    def _create_excel_bytes(self, headers, rows):
        """Helper to create an in-memory .xlsx file."""
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    # --------------------------------------------------------------------------
    # 1. Valid Curriculum Import
    # --------------------------------------------------------------------------
    def test_01_valid_curriculum_import(self):
        headers = ["Grade", "Subject", "Chapter", "Concept", "Chapter Order", "Chapter Difficulty", "Concept Order", "Concept Content"]
        rows = [
            ["Class 5", "Mathematics", "Geometry 3D", "Polygons & Vertices", 3, "easy", 1, "Polygons explanation."],
            ["Class 5", "Mathematics", "Geometry 3D", "Surface Areas", 3, "medium", 2, "Surface area formulas."]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        self.assertIsNone(err)

        valid_rows, errors, stats = ValidatorRegistry.validate_curriculum(raw_headers, parsed_rows)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(valid_rows), 2)
        self.assertEqual(stats["creates"], 2)

        job = BulkImportJob.objects.create(
            import_type="curriculum",
            filename="curriculum.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=valid_rows
        )
        ImportEngine.execute_import(job)

        topic = Topic.objects.get(title="Geometry 3D", grade=self.grade5, subject=self.subject_math)
        self.assertEqual(topic.concepts.count(), 2)
        self.assertTrue(Concept.objects.filter(topic=topic, title="Polygons & Vertices").exists())
        self.assertTrue(Concept.objects.filter(topic=topic, title="Surface Areas").exists())

    # --------------------------------------------------------------------------
    # 2. Invalid Curriculum Relationships
    # --------------------------------------------------------------------------
    def test_02_invalid_curriculum_relationships(self):
        # Trying to assign existing concept "Place Value Systems" (which belongs to "Number & Operations")
        # to a different chapter "Fractions & Decimals"
        headers = ["Grade", "Subject", "Chapter", "Concept"]
        rows = [
            ["Class 5", "Mathematics", "Fractions & Decimals", "Place Value Systems"]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_curriculum(raw_headers, parsed_rows)

        self.assertGreaterEqual(len(errors), 1)
        self.assertIn("already linked to chapter", errors[0]["error"])

    # --------------------------------------------------------------------------
    # 3. Valid Question Import
    # --------------------------------------------------------------------------
    def test_03_valid_question_import(self):
        headers = [
            "Grade", "Subject", "Chapter", "Concept", "Question Prompt",
            "Option A", "Option B", "Option C", "Option D",
            "Correct Answer", "Difficulty", "Marks", "Explanation", "Hint 1"
        ]
        rows = [
            [
                "Class 5", "Mathematics", "Number & Operations", "Place Value Systems",
                "What is the place value of 8 in 384,102?",
                "80,000", "8,000", "800", "80",
                "A", "easy", 2, "The 8 is in the ten-thousands place.", "Count digits from the right."
            ]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(valid_rows), 1)

        job = BulkImportJob.objects.create(
            import_type="questions",
            filename="test_q.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=valid_rows
        )
        ImportEngine.execute_import(job)

        q = Question.objects.get(prompt="What is the place value of 8 in 384,102?")
        self.assertEqual(q.marks, 2)
        self.assertEqual(q.options.count(), 4)
        correct_opt = q.options.get(is_correct=True)
        self.assertEqual(correct_opt.text, "80,000")
        self.assertEqual(q.hints.count(), 1)
        self.assertEqual(q.hints.first().text, "Count digits from the right.")

    # --------------------------------------------------------------------------
    # 4. Missing Required Column
    # --------------------------------------------------------------------------
    def test_04_missing_required_column(self):
        # Missing Option B and Correct Answer
        headers = ["Grade", "Subject", "Chapter", "Question Prompt", "Option A"]
        rows = [["Class 5", "Mathematics", "Number & Operations", "Test Q", "Opt 1"]]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)

        self.assertGreaterEqual(len(errors), 1)
        self.assertIn("Missing required column headers", errors[0]["error"])

    # --------------------------------------------------------------------------
    # 5. Invalid Correct Answer
    # --------------------------------------------------------------------------
    def test_05_invalid_correct_answer(self):
        headers = [
            "Grade", "Subject", "Chapter", "Question Prompt",
            "Option A", "Option B", "Option C", "Correct Answer"
        ]
        # Option D is not provided, but correct answer specifies "D"
        rows = [
            ["Class 5", "Mathematics", "Number & Operations", "What is 2+2?", "3", "4", "5", "D"]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)

        self.assertGreaterEqual(len(errors), 1)
        self.assertIn("does not match any provided options", errors[0]["error"])

    # --------------------------------------------------------------------------
    # 6. Invalid Grade / Subject / Chapter
    # --------------------------------------------------------------------------
    def test_06_invalid_academic_hierarchy(self):
        headers = [
            "Grade", "Subject", "Chapter", "Question Prompt",
            "Option A", "Option B", "Correct Answer"
        ]
        # Non-existent Grade
        rows = [
            ["Class 99", "Mathematics", "Number & Operations", "Prompt?", "A", "B", "A"]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)

        self.assertGreaterEqual(len(errors), 1)
        self.assertIn("Grade 'Class 99' does not exist", errors[0]["error"])

    # --------------------------------------------------------------------------
    # 7. Duplicate Handling (Skip / Flag)
    # --------------------------------------------------------------------------
    def test_07_duplicate_handling(self):
        headers = [
            "Grade", "Subject", "Chapter", "Question Prompt",
            "Option A", "Option B", "Correct Answer"
        ]
        # Two identical rows in the same spreadsheet
        rows = [
            ["Class 5", "Mathematics", "Number & Operations", "Unique prompt 123", "Yes", "No", "A"],
            ["Class 5", "Mathematics", "Number & Operations", "Unique prompt 123", "Yes", "No", "A"]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)

        self.assertEqual(len(errors), 0)
        self.assertEqual(stats["creates"], 1)
        self.assertEqual(stats["duplicates"], 1)
        self.assertEqual(valid_rows[1]["action"], "DUPLICATE")

    # --------------------------------------------------------------------------
    # 8. Create vs Update Behavior
    # --------------------------------------------------------------------------
    def test_08_create_vs_update_behavior(self):
        # First create question
        existing_q = Question.objects.create(
            topic=self.topic_numbers,
            prompt="Old Prompt Text",
            difficulty="easy",
            marks=1,
            status="published"
        )
        Option.objects.create(question=existing_q, text="Old A", is_correct=True, order=1)
        Option.objects.create(question=existing_q, text="Old B", is_correct=False, order=2)

        # Excel providing Question ID for update
        headers = [
            "Question ID", "Grade", "Subject", "Chapter", "Question Prompt",
            "Option A", "Option B", "Correct Answer", "Marks"
        ]
        rows = [
            [existing_q.id, "Class 5", "Mathematics", "Number & Operations", "New Updated Prompt Text", "New A", "New B", "B", 5]
        ]
        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)

        self.assertEqual(len(errors), 0)
        self.assertEqual(stats["updates"], 1)
        self.assertEqual(valid_rows[0]["action"], "UPDATE")

        job = BulkImportJob.objects.create(
            import_type="questions",
            filename="update_q.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=valid_rows
        )
        ImportEngine.execute_import(job)

        existing_q.refresh_from_db()
        self.assertEqual(existing_q.prompt, "New Updated Prompt Text")
        self.assertEqual(existing_q.marks, 5)
        # Option B is now the correct one
        opt_b = existing_q.options.get(text="New B")
        self.assertTrue(opt_b.is_correct)

    # --------------------------------------------------------------------------
    # 9. Atomic Rollback Guarantee
    # --------------------------------------------------------------------------
    def test_09_atomic_rollback_guarantee(self):
        initial_q_count = Question.objects.count()

        # Prepare a valid row and a second row that intentionally causes a database-level integrity error
        valid_row_1 = {
            "row_number": 2,
            "action": "CREATE",
            "topic_id": self.topic_numbers.id,
            "concept_id": None,
            "prompt": "Atomic Test Question 1",
            "explanation": "Exp 1",
            "difficulty": "easy",
            "allow_multiple_answers": False,
            "marks": 1,
            "negative_marks": 0,
            "options": [{"text": "Opt 1", "is_correct": True, "order": 1}, {"text": "Opt 2", "is_correct": False, "order": 2}],
            "hint": ""
        }
        # Row 2 with non-existent question_id that will trigger Question.DoesNotExist
        faulty_row_2 = {
            "row_number": 3,
            "action": "UPDATE",
            "question_id": 999999,  # Non-existent ID triggers Question.DoesNotExist
            "topic_id": self.topic_numbers.id,
            "concept_id": None,
            "prompt": "Atomic Test Question 2",
            "explanation": "",
            "difficulty": "easy",
            "allow_multiple_answers": False,
            "marks": 1,
            "negative_marks": 0,
            "options": [{"text": "A", "is_correct": True, "order": 1}],
            "hint": ""
        }

        job = BulkImportJob.objects.create(
            import_type="questions",
            filename="atomic_test.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=[valid_row_1, faulty_row_2]
        )

        with self.assertRaises(Exception):
            ImportEngine.execute_import(job)

        job.refresh_from_db()
        self.assertEqual(job.status, BulkImportJob.Status.ROLLED_BACK)
        # Verify that Question 1 was NOT committed
        self.assertEqual(Question.objects.count(), initial_q_count)
        self.assertFalse(Question.objects.filter(prompt="Atomic Test Question 1").exists())

    # --------------------------------------------------------------------------
    # 10. Security & Permission Checks
    # --------------------------------------------------------------------------
    def test_10_permission_checks(self):
        client = Client()

        # Anonymous user must be redirected to login
        hub_url = reverse("bulk_import:hub")
        res_anon = client.get(hub_url)
        self.assertEqual(res_anon.status_code, 302)
        self.assertIn("login", res_anon.url)

        # Student / non-staff user must be rejected
        client.force_login(self.student_user)
        res_student = client.get(hub_url)
        self.assertEqual(res_student.status_code, 302)

        # Superuser / Staff must have access
        client.force_login(self.admin_user)
        res_admin = client.get(hub_url)
        self.assertEqual(res_admin.status_code, 200)

    # --------------------------------------------------------------------------
    # 11. Large Import Dataset (100+ rows)
    # --------------------------------------------------------------------------
    def test_11_large_import_batch(self):
        headers = [
            "Grade", "Subject", "Chapter", "Question Prompt",
            "Option A", "Option B", "Option C", "Option D",
            "Correct Answer", "Difficulty", "Marks"
        ]
        rows = []
        for i in range(1, 101):
            rows.append([
                "Class 5", "Mathematics", "Number & Operations",
                f"Batch Question Prompt #{i} - What is {i} x 10?",
                str(i * 10), str(i * 10 + 1), str(i * 10 + 2), str(i * 10 + 3),
                "A", "easy", 1
            ])

        excel_file = self._create_excel_bytes(headers, rows)
        raw_headers, parsed_rows, err = ExcelService.parse_sheet_rows(excel_file)
        self.assertEqual(len(parsed_rows), 100)

        valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, parsed_rows)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(valid_rows), 100)

        job = BulkImportJob.objects.create(
            import_type="questions",
            filename="large_batch.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=valid_rows
        )
        ImportEngine.execute_import(job)

        job.refresh_from_db()
        self.assertEqual(job.status, BulkImportJob.Status.IMPORTED)
        self.assertEqual(job.created_count, 100)
        self.assertEqual(Question.objects.filter(prompt__startswith="Batch Question Prompt").count(), 100)

    # --------------------------------------------------------------------------
    # 12. Existing Admin Manual Creation Remains Intact
    # --------------------------------------------------------------------------
    def test_12_existing_admin_manual_workflow(self):
        # Verify manual creation of Concept with ConceptAdminForm logic
        from apps.curriculum.admin_forms import ConceptAdminForm
        form_data = {
            "grade": self.grade5.id,
            "subject": self.subject_math.id,
            "topic": self.topic_numbers.id,
            "title": "Manual Admin Concept",
            "content_body": "Created manually through Admin form.",
            "order": 10,
            "status": "published"
        }
        form = ConceptAdminForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        manual_concept = form.save()
        self.assertEqual(manual_concept.topic, self.topic_numbers)

        # Verify manual Question creation with Options
        manual_q = Question.objects.create(
            topic=self.topic_numbers,
            prompt="Manually entered question",
            explanation="Manual explanation",
            difficulty="medium",
            marks=2,
            status="published"
        )
        Option.objects.create(question=manual_q, text="Option 1", is_correct=True, order=1)
        Option.objects.create(question=manual_q, text="Option 2", is_correct=False, order=2)

        self.assertEqual(manual_q.options.count(), 2)

    # --------------------------------------------------------------------------
    # 13. Game Content & Quizzes Imports
    # --------------------------------------------------------------------------
    def test_13_game_content_and_quizzes_imports(self):
        # A. Game Content
        gc_headers = ["Game Title", "Step Order", "Prompt", "Content Type", "Points", "Target Data (JSON)"]
        gc_rows = [
            ["Pizza Fraction Challenge", 1, "Serve 1/2 of pizza", "fraction_slice", 10, '{"slices": 2}']
        ]
        excel_file = self._create_excel_bytes(gc_headers, gc_rows)
        raw_headers, parsed_rows, _ = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_game_content(raw_headers, parsed_rows)
        self.assertEqual(len(errors), 0)

        job_gc = BulkImportJob.objects.create(
            import_type="game_content",
            filename="gc.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=valid_rows
        )
        ImportEngine.execute_import(job_gc)
        self.assertTrue(GameContent.objects.filter(game=self.game_pizza, order=1).exists())

        # B. Quizzes Import
        quiz_headers = [
            "Quiz Title", "Grade", "Subject", "Chapter", "Quiz Duration (Mins)",
            "Question Prompt", "Option A", "Option B", "Correct Answer"
        ]
        quiz_rows = [
            ["Weekly Mock Exam 1", "Class 5", "Mathematics", "Number & Operations", 30, "What is 100 - 45?", "55", "65", "A"]
        ]
        excel_file = self._create_excel_bytes(quiz_headers, quiz_rows)
        raw_headers, parsed_rows, _ = ExcelService.parse_sheet_rows(excel_file)
        valid_rows, errors, stats = ValidatorRegistry.validate_quizzes(raw_headers, parsed_rows)
        self.assertEqual(len(errors), 0)

        job_quiz = BulkImportJob.objects.create(
            import_type="quizzes",
            filename="quiz.xlsx",
            status=BulkImportJob.Status.VALIDATED,
            all_parsed_rows=valid_rows
        )
        ImportEngine.execute_import(job_quiz)

        quiz = Quiz.objects.get(title="Weekly Mock Exam 1")
        self.assertEqual(quiz.duration_seconds, 30 * 60)
        self.assertEqual(quiz.questions.count(), 1)
