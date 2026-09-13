from rest_framework import serializers

from .models import Game


class GameSerializer(serializers.ModelSerializer):
    concept_title = serializers.CharField(source="concept.title", read_only=True, default=None)
    topic_title = serializers.CharField(source="concept.topic.title", read_only=True, default=None)
    subject_name = serializers.CharField(source="concept.topic.subject.name", read_only=True, default=None)
    grade_name = serializers.CharField(source="concept.topic.grade.name", read_only=True, default=None)

    class Meta:
        model = Game
        fields = [
            "id", "public_id", "title", "description",
            "game_type", "difficulty", "access_tier", "config",
            "concept", "concept_title", "topic_title",
            "subject_name", "grade_name", "status", "created_at",
        ]
        read_only_fields = ["id", "public_id", "status", "created_at"]