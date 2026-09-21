from rest_framework import serializers
from .models import MockTest, MockTestQuestion, MockTestAttempt, MockTestResponse, Question, Option


class OptionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text", "order"]


class QuestionPublicSerializer(serializers.ModelSerializer):
    options = OptionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "prompt",
            "difficulty",
            "allow_multiple_answers",
            "marks",
            "negative_marks",
            "options",
        ]


class MockTestListSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True, default=None)
    question_count = serializers.IntegerField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    best_score = serializers.SerializerMethodField()
    best_percentage = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()
    last_attempt_status = serializers.SerializerMethodField()

    class Meta:
        model = MockTest
        fields = [
            "id",
            "public_id",
            "title",
            "description",
            "grade",
            "grade_name",
            "subject",
            "subject_name",
            "duration_seconds",
            "duration_minutes",
            "question_count",
            "passing_percentage",
            "best_score",
            "best_percentage",
            "attempts_count",
            "last_attempt_status",
            "status",
        ]

    def get_best_score(self, obj):
        student = self.context.get("student")
        if not student:
            return None
        best = obj.attempts.filter(student=student, status="submitted").order_by("-score").first()
        return best.score if best else None

    def get_best_percentage(self, obj):
        student = self.context.get("student")
        if not student:
            return None
        best = obj.attempts.filter(student=student, status="submitted").order_by("-percentage").first()
        return best.percentage if best else None

    def get_attempts_count(self, obj):
        student = self.context.get("student")
        if not student:
            return 0
        return obj.attempts.filter(student=student, status="submitted").count()

    def get_last_attempt_status(self, obj):
        student = self.context.get("student")
        if not student:
            return None
        last = obj.attempts.filter(student=student).order_by("-started_at").first()
        return last.status if last else None


class MockTestDetailSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True, default=None)
    questions = serializers.SerializerMethodField()
    question_count = serializers.IntegerField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = MockTest
        fields = [
            "id",
            "public_id",
            "title",
            "description",
            "grade",
            "grade_name",
            "subject",
            "subject_name",
            "duration_seconds",
            "duration_minutes",
            "question_count",
            "passing_percentage",
            "questions",
        ]

    def get_questions(self, obj):
        test_questions = obj.test_questions.select_related("question").prefetch_related("question__options").order_by("order", "id")
        questions_list = []
        for tq in test_questions:
            q_data = QuestionPublicSerializer(tq.question).data
            q_data["test_order"] = tq.order
            questions_list.append(q_data)
        return questions_list
