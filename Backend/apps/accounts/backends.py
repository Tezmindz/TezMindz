from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from .models import StudentProfile
from .utils import normalize_phone_number

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    
    Supports authenticating with:
    1. Email (case-insensitive)
    2. Phone number (normalized to E.164 via StudentProfile)
    3. Legacy / internal username (for staff, admin, demo, and test accounts)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (
            username
            or kwargs.get("email")
            or kwargs.get("phone")
            or kwargs.get("phone_number")
            or kwargs.get("identifier")
            or ""
        )
        if not identifier or not password:
            return None

        identifier = str(identifier).strip()
        user = None

        # 1. Check if identifier is an email address
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()

        # 2. Check if identifier is a valid normalized phone number
        if user is None:
            normalized_phone = normalize_phone_number(identifier)
            if normalized_phone:
                profile = (
                    StudentProfile.objects.filter(phone_number=normalized_phone)
                    .select_related("user")
                    .first()
                )
                if profile and profile.user:
                    user = profile.user

        # 3. Fallback: Check username for staff, admin, demo, and existing internal accounts
        if user is None:
            user = User.objects.filter(username=identifier).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
