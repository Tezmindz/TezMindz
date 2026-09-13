from django import forms
from django.core.exceptions import ValidationError
from .models import Grade, Subject, Topic, Concept


class ConceptAdminForm(forms.ModelForm):
    """
    Step-by-step dependent selection for Concept:
    Step 1: Grade
    Step 2: Subject (filtered by Grade)
    Step 3: Chapter (Topic, filtered by Grade + Subject)
    Then: Concept fields (title, content_body, order, status, published_at).

    Validates hierarchy consistency server-side to guarantee zero tamper data.
    """
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.all().order_by("order"),
        required=True,
        label="Grade / Class",
        help_text="Step 1: Select Grade to filter Subjects."
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by("order", "name"),
        required=True,
        label="Subject",
        help_text="Step 2: Select Subject belonging to the selected Grade."
    )

    class Meta:
        model = Concept
        fields = [
            "grade",
            "subject",
            "topic",
            "title",
            "content_body",
            "order",
            "status",
            "published_at",
        ]
        labels = {
            "topic": "Chapter (Topic)",
        }
        help_texts = {
            "topic": "Step 3: Select Chapter belonging to the selected Grade and Subject.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic"].queryset = Topic.objects.all()

        # In edit mode, pre-populate Grade and Subject from the existing Topic
        if self.instance and self.instance.pk and self.instance.topic:
            topic = self.instance.topic
            self.initial["grade"] = topic.grade_id
            self.initial["subject"] = topic.subject_id

            # Filter valid choices for initial render
            self.fields["subject"].queryset = Subject.objects.filter(
                topics__grade=topic.grade
            ).distinct().order_by("order", "name")
            self.fields["topic"].queryset = Topic.objects.filter(
                grade=topic.grade, subject=topic.subject
            ).order_by("order", "title")
        elif self.data:
            # Handle bound data during POST
            grade_id = self.data.get("grade")
            subject_id = self.data.get("subject")
            if grade_id:
                self.fields["subject"].queryset = Subject.objects.filter(
                    topics__grade_id=grade_id
                ).distinct().order_by("order", "name")
            if grade_id and subject_id:
                self.fields["topic"].queryset = Topic.objects.filter(
                    grade_id=grade_id, subject_id=subject_id
                ).order_by("order", "title")

    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get("grade")
        subject = cleaned_data.get("subject")
        topic = cleaned_data.get("topic")

        if not topic:
            raise ValidationError({"topic": "A valid Chapter must be selected."})

        if grade and topic.grade_id != grade.id:
            raise ValidationError({
                "topic": f"Selected chapter '{topic.title}' belongs to {topic.grade}, not {grade}."
            })

        if subject and topic.subject_id != subject.id:
            raise ValidationError({
                "topic": f"Selected chapter '{topic.title}' belongs to {topic.subject}, not {subject}."
            })

        return cleaned_data
