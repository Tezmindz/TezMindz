from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User, StudentProfile
from apps.accounts.utils import normalize_phone_number, generate_internal_username
from apps.curriculum.models import Grade


class PhoneNormalizationTests(TestCase):
    def test_indian_10_digit_number(self):
        self.assertEqual(normalize_phone_number("9876543210"), "+919876543210")

    def test_indian_with_plus_91(self):
        self.assertEqual(normalize_phone_number("+919876543210"), "+919876543210")

    def test_indian_with_91_prefix(self):
        self.assertEqual(normalize_phone_number("919876543210"), "+919876543210")

    def test_indian_with_zero_prefix(self):
        self.assertEqual(normalize_phone_number("09876543210"), "+919876543210")

    def test_indian_with_spaces_and_hyphens(self):
        self.assertEqual(normalize_phone_number("+91 98765-43210"), "+919876543210")
        self.assertEqual(normalize_phone_number("98765 43210"), "+919876543210")

    def test_invalid_numbers(self):
        self.assertIsNone(normalize_phone_number(""))
        self.assertIsNone(normalize_phone_number("12345"))
        self.assertIsNone(normalize_phone_number("abcdefghij"))
        self.assertIsNone(normalize_phone_number("1234567890"))  # Starts with 1 (not a valid Indian mobile start)

    def test_generate_internal_username(self):
        u1 = generate_internal_username("Aarav Sharma")
        self.assertTrue(u1.startswith("aaravsharm_") or u1.startswith("student_"))
        self.assertNotIn("9876543210", u1)
        u2 = generate_internal_username("Aarav Sharma")
        self.assertNotEqual(u1, u2)


class StudentAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.grade = Grade.objects.create(name="Grade 5", order=5)

        # Existing student 1
        self.student_user = User.objects.create_user(
            username="student_aarav_abc123",
            email="aarav@tezmindz.com",
            password="password123",
            first_name="Aarav",
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            display_name="Aarav Sharma",
            phone_number="+919876543210",
            grade=self.grade,
        )

        # Existing student without phone number (legacy record)
        self.legacy_user = User.objects.create_user(
            username="legacy_student",
            email="legacy@tezmindz.com",
            password="legacypassword123",
            first_name="Legacy Student",
        )
        self.legacy_profile = StudentProfile.objects.create(
            user=self.legacy_user,
            display_name="Legacy Student",
            phone_number=None,
            grade=self.grade,
        )

        # Admin user
        self.admin_user = User.objects.create_superuser(
            username="admin_super",
            email="admin@tezmindz.com",
            password="adminpassword123",
        )

    # 1. Registration with phone + email
    def test_registration_with_phone_and_email(self):
        response = self.client.post(
            reverse("common:register"),
            data={
                "name": "Priya Patel",
                "phone": "9811122233",
                "email": "priya@tezmindz.com",
                "classLevel": 5,
                "password": "priyapassword123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("access", data)
        self.assertIn("refresh", data)

        created_user = User.objects.get(email="priya@tezmindz.com")
        self.assertTrue(created_user.username)
        self.assertNotIn("9811122233", created_user.username)
        self.assertEqual(created_user.student_profile.phone_number, "+919811122233")
        self.assertEqual(created_user.student_profile.display_name, "Priya Patel")

    # 2. Registration without manually supplied username
    def test_registration_generates_safe_internal_username(self):
        response = self.client.post(
            reverse("common:register"),
            data={
                "name": "Rohan Gupta",
                "phone": "9822233344",
                "email": "rohan@tezmindz.com",
                "classLevel": 5,
                "password": "rohanpassword123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email="rohan@tezmindz.com")
        self.assertTrue(user.username.startswith("rohangupta_") or user.username.startswith("student_"))

    # 3. Duplicate phone rejected
    def test_duplicate_phone_rejected(self):
        response = self.client.post(
            reverse("common:register"),
            data={
                "name": "Duplicate Phone Student",
                "phone": "9876543210",  # Same as aarav
                "email": "different_email@tezmindz.com",
                "classLevel": 5,
                "password": "password123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("That phone number is already registered", response.json().get("message", ""))

    # 4. Duplicate email rejected
    def test_duplicate_email_rejected(self):
        response = self.client.post(
            reverse("common:register"),
            data={
                "name": "Duplicate Email Student",
                "phone": "9833344455",
                "email": "aarav@tezmindz.com",  # Same as aarav
                "classLevel": 5,
                "password": "password123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("That email is already registered", response.json().get("message", ""))

    # 5. Login with email + password
    def test_login_with_email_and_password(self):
        response = self.client.post(
            reverse("common:login"),
            data={"email": "aarav@tezmindz.com", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("redirect_url"), "/dashboard/")
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    # 6. Login with phone + password
    def test_login_with_phone_and_password(self):
        # 10-digit input
        response = self.client.post(
            reverse("common:login"),
            data={"email": "9876543210", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))

        # +91 prefixed input
        response2 = self.client.post(
            reverse("common:login"),
            data={"email": "+919876543210", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(response2.json().get("success"))

    # 7. Invalid phone/email + password rejected generically
    def test_invalid_credentials_rejected(self):
        # Wrong password
        response = self.client.post(
            reverse("common:login"),
            data={"email": "aarav@tezmindz.com", "password": "wrongpassword"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid email/phone or password", response.json().get("message", ""))

        # Non-existent phone
        response_nonexistent = self.client.post(
            reverse("common:login"),
            data={"email": "9899999999", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response_nonexistent.status_code, 400)
        self.assertIn("Invalid email/phone or password", response_nonexistent.json().get("message", ""))

    # 8. Existing username-based internal users remain functional
    def test_internal_username_fallback(self):
        # Demo user / existing username
        demo_user = User.objects.create_user(
            username="student",
            email="student@demo.com",
            password="password123",
        )
        StudentProfile.objects.create(user=demo_user, display_name="Demo", grade=self.grade)
        response = self.client.post(
            reverse("common:login"),
            data={"email": "student", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))

    # 9. JWT access token generation works (with email and phone)
    def test_jwt_obtain_with_email_and_phone(self):
        # Obtain with email
        res_email = self.client.post(
            reverse("jwt-create"),
            data={"email": "aarav@tezmindz.com", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(res_email.status_code, 200)
        self.assertIn("access", res_email.json())
        self.assertIn("refresh", res_email.json())

        # Obtain with phone
        res_phone = self.client.post(
            reverse("jwt-create"),
            data={"phone": "9876543210", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(res_phone.status_code, 200)
        self.assertIn("access", res_phone.json())
        self.assertIn("refresh", res_phone.json())

        # Obtain with identifier field
        res_ident = self.client.post(
            reverse("jwt-create"),
            data={"identifier": "+919876543210", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(res_ident.status_code, 200)
        self.assertIn("access", res_ident.json())

    # 10. JWT refresh works
    def test_jwt_refresh(self):
        res_login = self.client.post(
            reverse("jwt-create"),
            data={"email": "aarav@tezmindz.com", "password": "password123"},
            content_type="application/json",
        )
        refresh_token = res_login.json()["refresh"]

        res_refresh = self.client.post(
            reverse("jwt-refresh"),
            data={"refresh": refresh_token},
            content_type="application/json",
        )
        self.assertEqual(res_refresh.status_code, 200)
        self.assertIn("access", res_refresh.json())

    # 11. Session login works
    def test_session_login_sets_session(self):
        response = self.client.post(
            reverse("common:login"),
            data={"email": "aarav@tezmindz.com", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        # Dashboard should now be accessible without redirect
        dash_res = self.client.get(reverse("common:dashboard"))
        self.assertEqual(dash_res.status_code, 200)

    # 12. Student cannot authenticate as another account by manipulating phone/email
    def test_cross_account_protection(self):
        response = self.client.post(
            reverse("common:login"),
            data={"email": "aarav@tezmindz.com", "password": "legacypassword123"},  # Legacy user's password
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get("success"))

    # 13. Admin/staff login still works
    def test_admin_staff_login_still_works(self):
        # Admin cannot login on student login page
        res_student_login = self.client.post(
            reverse("common:login"),
            data={"email": "admin@tezmindz.com", "password": "adminpassword123"},
            content_type="application/json",
        )
        self.assertEqual(res_student_login.status_code, 403)

        # Admin CAN login on admin portal with username
        res_admin_username = self.client.post(
            reverse("common:tezadmin_login"),
            data={"identifier": "admin_super", "password": "adminpassword123"},
            content_type="application/json",
        )
        self.assertEqual(res_admin_username.status_code, 200)
        self.assertTrue(res_admin_username.json().get("success"))

        # Admin CAN login on admin portal with email
        res_admin_email = self.client.post(
            reverse("common:tezadmin_login"),
            data={"identifier": "admin@tezmindz.com", "password": "adminpassword123"},
            content_type="application/json",
        )
        self.assertEqual(res_admin_email.status_code, 200)
        self.assertTrue(res_admin_email.json().get("success"))

    # 14. Existing users without phone numbers are not broken
    def test_existing_users_without_phone_still_work(self):
        response = self.client.post(
            reverse("common:login"),
            data={"email": "legacy@tezmindz.com", "password": "legacypassword123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))
