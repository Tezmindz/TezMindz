from rest_framework import serializers
from .models import Badge, StudentBadge


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "code", "name", "description", "icon_key", "is_active"]


class StudentBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = StudentBadge
        fields = ["id", "badge", "earned_at"]
