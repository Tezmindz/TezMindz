from django import forms
from django.core.exceptions import ValidationError
from apps.curriculum.models import Grade, Subject, Topic, Concept
from .models import Game
from .plugins import get_plugin_choices


class GameAdminForm(forms.ModelForm):
    """
    Step-by-step dependent selection for Game:
    Step 1: Grade
    Step 2: Subject (filtered by Grade)
    Step 3: Chapter (filtered by Grade + Subject)
    Step 4: Concept (filtered by Chapter)
    Then: Game fields (title, description, game_type, difficulty, access_tier, config, status, published_at).

    Validates hierarchy consistency server-side.
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
    chapter = forms.ModelChoiceField(
        queryset=Topic.objects.all().order_by("order", "title"),
        required=True,
        label="Chapter",
        help_text="Step 3: Select Chapter belonging to the selected Grade and Subject."
    )
    game_type = forms.ChoiceField(
        choices=get_plugin_choices,
        required=True,
        label="Game Type / Template",
        help_text="Select a game plugin template from frontend/static/games/plugins/.",
        widget=forms.Select(attrs={"class": "vSelectField", "style": "min-width: 320px;"})
    )

    class Meta:
        model = Game
        fields = [
            "grade",
            "subject",
            "chapter",
            "concept",
            "title",
            "description",
            "game_type",
            "difficulty",
            "access_tier",
            "config",
            "status",
            "published_at",
        ]
        labels = {
            "concept": "Concept",
        }
        help_texts = {
            "concept": "Step 4: Select Concept belonging to the selected Chapter.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plugin_choices = list(get_plugin_choices())
        choices_list = [("", "--------- Select Game Template ---------")] + plugin_choices

        # If editing an existing game whose type is custom/legacy, preserve it in choices
        if self.instance and self.instance.pk and self.instance.game_type:
            current_type = self.instance.game_type
            if not any(c[0] == current_type for c in plugin_choices):
                choices_list.append((current_type, f"{current_type} (Custom / Legacy)"))

        self.fields["game_type"].choices = choices_list
        self.fields["concept"].queryset = Concept.objects.all()

        # In edit mode, pre-populate Grade, Subject, Chapter from the existing Concept
        if self.instance and self.instance.pk and self.instance.concept:
            concept = self.instance.concept
            topic = concept.topic
            self.initial["grade"] = topic.grade_id
            self.initial["subject"] = topic.subject_id
            self.initial["chapter"] = topic.id

            self.fields["subject"].queryset = Subject.objects.filter(
                topics__grade=topic.grade
            ).distinct().order_by("order", "name")
            self.fields["chapter"].queryset = Topic.objects.filter(
                grade=topic.grade, subject=topic.subject
            ).order_by("order", "title")
            self.fields["concept"].queryset = Concept.objects.filter(
                topic=topic
            ).order_by("order", "title")
        elif self.data:
            grade_id = self.data.get("grade")
            subject_id = self.data.get("subject")
            chapter_id = self.data.get("chapter")
            if grade_id:
                self.fields["subject"].queryset = Subject.objects.filter(
                    topics__grade_id=grade_id
                ).distinct().order_by("order", "name")
            if grade_id and subject_id:
                self.fields["chapter"].queryset = Topic.objects.filter(
                    grade_id=grade_id, subject_id=subject_id
                ).order_by("order", "title")
            if chapter_id:
                self.fields["concept"].queryset = Concept.objects.filter(
                    topic_id=chapter_id
                ).order_by("order", "title")

    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get("grade")
        subject = cleaned_data.get("subject")
        chapter = cleaned_data.get("chapter")
        concept = cleaned_data.get("concept")

        if not concept:
            raise ValidationError({"concept": "A valid Concept must be selected."})

        if chapter and concept.topic_id != chapter.id:
            raise ValidationError({
                "concept": f"Selected concept '{concept.title}' belongs to chapter '{concept.topic.title}', not '{chapter.title}'."
            })

        if subject and concept.topic.subject_id != subject.id:
            raise ValidationError({
                "chapter": f"Selected chapter '{concept.topic.title}' belongs to subject '{concept.topic.subject.name}', not '{subject.name}'."
            })

        if grade and concept.topic.grade_id != grade.id:
            raise ValidationError({
                "grade": f"Selected chapter '{concept.topic.title}' belongs to grade '{concept.topic.grade.name}', not '{grade.name}'."
            })

        return cleaned_data
