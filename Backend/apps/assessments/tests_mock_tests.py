import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.assessments.models import Question, Option, MockTest, MockTestQuestion, MockTestAttempt, MockTestResponse
from apps.accounts.models import StudentProfile

User = get_user_model()


class MockTestSecurityAndScoringTests(TestCase):
    def setUp(self):
        # 1. Setup Grades & Subjects
        self.grade5 = Grade.objects.create(name="5", order=5)
        self.grade6 = Grade.objects.create(name="6", order=6)
        
        self.math = Subject.objects.create(name="Mathematics", slug="math", order=1)
        self.topic5 = Topic.objects.create(grade=self.grade5, subject=self.math, title="Fractions", order=1)
        self.concept5 = Concept.objects.create(topic=self.topic5, title="Intro to Fractions", order=1)

        # 2. Setup Students
        self.user5 = User.objects.create_user(username="student5", password="password123", email="s5@test.com")
        self.profile5 = StudentProfile.objects.create(user=self.user5, grade=self.grade5, display_name="Hero 5")

        self.user6 = User.objects.create_user(username="student6", password="password123", email="s6@test.com")
        self.profile6 = StudentProfile.objects.create(user=self.user6, grade=self.grade6, display_name="Hero 6")

        # 3. Setup Questions
        self.q1 = Question.objects.create(
            topic=self.topic5,
            concept=self.concept5,
            prompt="What is 1/2 + 1/2?",
            difficulty="easy",
            marks=4,
            negative_marks=1,
            explanation="1/2 + 1/2 = 1",
            status="published",
        )
        self.q1_opt_correct = Option.objects.create(question=self.q1, text="1", is_correct=True, order=1)
        self.q1_opt_wrong = Option.objects.create(question=self.q1, text="2", is_correct=False, order=2)

        self.q2 = Question.objects.create(
            topic=self.topic5,
            concept=self.concept5,
            prompt="What is 1/4 + 1/4?",
            difficulty="medium",
            marks=4,
            negative_marks=1,
            explanation="2/4 = 1/2",
            status="published",
        )
        self.q2_opt_correct = Option.objects.create(question=self.q2, text="1/2", is_correct=True, order=1)
        self.q2_opt_wrong = Option.objects.create(question=self.q2, text="3/4", is_correct=False, order=2)

        # 4. Setup Mock Tests
        self.mock_test_g5 = MockTest.objects.create(
            title="Grade 5 Math Grand Arena",
            grade=self.grade5,
            subject=self.math,
            duration_seconds=1800,
            passing_percentage=50,
            status="published",
        )
        MockTestQuestion.objects.create(mock_test=self.mock_test_g5, question=self.q1, order=1)
        MockTestQuestion.objects.create(mock_test=self.mock_test_g5, question=self.q2, order=2)

        self.mock_test_g6 = MockTest.objects.create(
            title="Grade 6 Advanced Olympiad",
            grade=self.grade6,
            duration_seconds=2700,
            status="published",
        )

        self.mock_test_draft = MockTest.objects.create(
            title="Grade 5 Unreleased Draft",
            grade=self.grade5,
            duration_seconds=1200,
            status="draft",
        )

        self.client5 = Client()
        self.client5.force_login(self.user5)

        self.client6 = Client()
        self.client6.force_login(self.user6)

    def test_grade_5_student_only_sees_grade_5_published_tests_in_api(self):
        """Student in Grade 5 must only receive Grade 5 published mock tests."""
        response = self.client5.get("/api/mock-tests/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data.get("results", [])
        test_ids = [t["id"] for t in results]

        self.assertIn(self.mock_test_g5.id, test_ids)
        self.assertNotIn(self.mock_test_g6.id, test_ids, "Grade 6 test must be hidden from Grade 5 student")
        self.assertNotIn(self.mock_test_draft.id, test_ids, "Draft test must never be visible to students")

    def test_grade_5_student_blocked_from_accessing_grade_6_test_by_id(self):
        """Direct URL/API query with another grade's test ID must return 404 Not Found."""
        response = self.client5.get(f"/api/mock-tests/{self.mock_test_g6.id}/")
        self.assertEqual(response.status_code, 404)

        # Also via HTML route
        html_resp = self.client5.get(f"/mock-tests/{self.mock_test_g6.id}/")
        self.assertEqual(html_resp.status_code, 404)

    def test_options_do_not_leak_correct_answers_before_submission(self):
        """Mock test questions and options payload must NEVER disclose is_correct."""
        response = self.client5.get(f"/api/mock-tests/{self.mock_test_g5.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        questions = data["mock_test"]["questions"]
        self.assertEqual(len(questions), 2)
        
        for q in questions:
            for opt in q["options"]:
                self.assertNotIn("is_correct", opt, "is_correct must NOT be present in options payload")

    def test_server_side_scoring_calculation(self):
        """Server must calculate score based on verified DB is_correct and positive/negative marks."""
        # Student answers Q1 correctly (+4) and Q2 incorrectly (-1) -> Score = 3
        payload = {
            "answers": {
                str(self.q1.id): self.q1_opt_correct.id,
                str(self.q2.id): self.q2_opt_wrong.id,
            },
            "time_taken_seconds": 37,
        }
        response = self.client5.post(
            f"/api/mock-tests/{self.mock_test_g5.id}/submit/",
            json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["score"], 3)
        self.assertEqual(data["correct_count"], 1)
        self.assertEqual(data["wrong_count"], 1)
        self.assertEqual(data["unanswered_count"], 0)
        self.assertEqual(data["total_marks"], 8)
        self.assertEqual(data["percentage"], 37)  # 3/8 = 37.5% -> int 37

        # Check DB attempt and responses
        attempt = MockTestAttempt.objects.get(public_id=data["attempt_id"])
        self.assertEqual(attempt.student, self.profile5)
        self.assertEqual(attempt.score, 3)
        self.assertEqual(MockTestResponse.objects.filter(attempt=attempt).count(), 2)

    def test_student_cannot_access_another_students_result(self):
        """A student cannot view another student's test results."""
        attempt = MockTestAttempt.objects.create(
            mock_test=self.mock_test_g5,
            student=self.profile5,
            score=8,
            total_marks=8,
            percentage=100,
            status="submitted",
        )

        # Student 6 tries to view Student 5's attempt
        self.client.force_login(self.user6)
        response = self.client.get(f"/mock-tests/result/{attempt.public_id}/")
        self.assertEqual(response.status_code, 404)
