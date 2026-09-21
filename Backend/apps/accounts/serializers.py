from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    grade_id = serializers.IntegerField(source="grade.id", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "display_name", "phone_number", "grade", "grade_name", "grade_id",
            "avatar_key", "xp_points", "adventure_coins", "daily_streak",
            "account_status", "created_at", "updated_at",
        ]
        read_only_fields = [
            "xp_points", "adventure_coins", "daily_streak",
            "account_status", "created_at", "updated_at",
        ]


class UserMeSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "student_profile"]
        read_only_fields = ["id", "username", "email", "role"]


class EmailOrPhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom TokenObtainPairSerializer allowing authentication via:
    - email + password
    - phone number + password
    - username + password (internal / staff / legacy fallback)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(required=False)
        self.fields["email"] = serializers.CharField(required=False)
        self.fields["phone"] = serializers.CharField(required=False)
        self.fields["phone_number"] = serializers.CharField(required=False)
        self.fields["identifier"] = serializers.CharField(required=False)

    def validate(self, attrs):
        identifier = (
            attrs.get("email")
            or attrs.get("phone")
            or attrs.get("phone_number")
            or attrs.get("identifier")
            or attrs.get(self.username_field)
            or ""
        ).strip()

        if not identifier:
            raise serializers.ValidationError({"detail": ["Email or phone number is required."]})

        attrs[self.username_field] = identifier
        return super().validate(attrs)
