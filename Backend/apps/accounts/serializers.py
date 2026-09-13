from rest_framework import serializers
from .models import User, StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    grade_id = serializers.IntegerField(source="grade.id", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "display_name", "grade", "grade_name", "grade_id",
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
