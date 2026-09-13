from rest_framework import serializers
from .models import TopicProgress


class TopicProgressSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    topic_id = serializers.IntegerField(source="topic.id", read_only=True)
    subject_name = serializers.CharField(source="topic.subject.name", read_only=True)
    grade_name = serializers.CharField(source="topic.grade.name", read_only=True)
    accuracy = serializers.FloatField(read_only=True)

    class Meta:
        model = TopicProgress
        fields = [
            "id", "topic_id", "topic_title", "subject_name", "grade_name",
            "attempts", "correct_count", "incorrect_count", "best_score",
            "accuracy", "last_activity_at",
        ]
