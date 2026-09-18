from django.db import IntegrityError, transaction
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
import json

from apps.accounts.models import StudentProfile, User
from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.games.models import Game
from apps.subscriptions.models import Plan, Subscription, Payment, TrialGameLog
from apps.subscriptions.services import can_student_access_game


class TrialGameLogTests(TestCase):
    def setUp(self):
        grade = Grade.objects.create(name="Grade 4", order=4)
        subject = Subject.objects.create(name="Mathematics", slug="mathematics")
        topic = Topic.objects.create(subject=subject, grade=grade, title="Fractions")
        concept = Concept.objects.create(topic=topic, title="Fraction Pizza", content_body="Learn fractions")
        self.game = Game.objects.create(concept=concept, title="Pizza Fraction Challenge", access_tier="trial")
        user = User.objects.create_user(username="aarav_test", email="aarav_test@example.com", password="testpass123")
        self.student = StudentProfile.objects.create(user=user, display_name="Aarav", grade=grade)

    def test_replaying_the_same_game_does_not_create_a_second_trial_slot(self):
        TrialGameLog.objects.create(student=self.student, game=self.game)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TrialGameLog.objects.create(student=self.student, game=self.game)

        self.assertEqual(TrialGameLog.objects.filter(student=self.student).count(), 1)


class SubscriptionApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.grade = Grade.objects.create(name="Grade 4", order=4)
        self.user = User.objects.create_user(username="teststudent", email="student@test.com", password="password123")
        self.student = StudentProfile.objects.create(user=self.user, display_name="Test Student", grade=self.grade)
        
        # Clean existing plans if any and create test plans
        Plan.objects.all().delete()
        self.plan1 = Plan.objects.create(
            name="Online only (Grade 1–4)",
            code="online-g14",
            price=299.00,
            billing_period="monthly",
            is_active=True,
            features={"badge": "Online Only", "grade_band": "Grade 1–4"}
        )
        self.plan2 = Plan.objects.create(
            name="Physical Centre + Online (Grade 1–4)",
            code="hybrid-g14",
            price=999.00,
            billing_period="monthly",
            is_active=True,
            features={"badge": "Centre + Online", "grade_band": "Grade 1–4"}
        )

    def test_get_plans_list(self):
        response = self.client.get("/api/subscriptions/plans/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["code"], "online-g14")

    def test_subscribe_plan_flow(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/subscriptions/subscribe/",
            data=json.dumps({"plan_id": self.plan1.id, "payment_method": "UPI", "auto_renew": True}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["subscription"]["plan"]["id"], self.plan1.id)
        self.assertEqual(res_data["subscription"]["status"], "active")

        # Verify current subscription endpoint
        current_res = self.client.get("/api/subscriptions/current/")
        self.assertEqual(current_res.status_code, 200)
        curr_data = current_res.json()
        self.assertTrue(curr_data["has_active_subscription"])
        self.assertEqual(curr_data["subscription"]["plan"]["id"], self.plan1.id)

    def test_upgrade_subscription(self):
        self.client.force_login(self.user)
        # Initial subscription
        self.client.post(
            "/api/subscriptions/subscribe/",
            data=json.dumps({"plan_id": self.plan1.id, "payment_method": "UPI"}),
            content_type="application/json"
        )
        # Upgrade to plan2
        upg_res = self.client.post(
            "/api/subscriptions/upgrade/",
            data=json.dumps({"plan_id": self.plan2.id, "payment_method": "CARD"}),
            content_type="application/json"
        )
        self.assertEqual(upg_res.status_code, 200)
        upg_data = upg_res.json()
        self.assertTrue(upg_data["success"])
        self.assertEqual(upg_data["subscription"]["plan"]["id"], self.plan2.id)

    def test_cancel_subscription(self):
        self.client.force_login(self.user)
        self.client.post(
            "/api/subscriptions/subscribe/",
            data=json.dumps({"plan_id": self.plan1.id, "payment_method": "UPI", "auto_renew": True}),
            content_type="application/json"
        )
        cancel_res = self.client.post("/api/subscriptions/cancel/")
        self.assertEqual(cancel_res.status_code, 200)
        c_data = cancel_res.json()
        self.assertTrue(c_data["success"])
        self.assertFalse(c_data["subscription"]["auto_renew"])

    def test_access_control_service(self):
        subject = Subject.objects.create(name="Science", slug="science")
        topic = Topic.objects.create(subject=subject, grade=self.grade, title="Physics")
        concept = Concept.objects.create(topic=topic, title="Energy", content_body="Energy")
        premium_game = Game.objects.create(concept=concept, title="Quantum Portal", access_tier="premium")
        trial_game = Game.objects.create(concept=concept, title="Energy Rush", access_tier="trial")

        # Without subscription
        self.assertFalse(can_student_access_game(self.student, premium_game))
        self.assertTrue(can_student_access_game(self.student, trial_game))

        # After subscribing
        Subscription.objects.create(
            student=self.student,
            plan=self.plan1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            status=Subscription.Status.ACTIVE
        )
        self.assertTrue(can_student_access_game(self.student, premium_game))
        self.assertTrue(can_student_access_game(self.student, trial_game))
