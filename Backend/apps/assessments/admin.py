from django.contrib import admin

from .models import Hint, Option, Question, QuestionResponse, Quiz, QuizAttempt, QuizQuestion


class OptionInline(admin.TabularInline):
	model = Option
	extra = 2
	fields = ("text", "is_correct", "order")


class HintInline(admin.TabularInline):
	model = Hint
	extra = 0
	fields = ("text", "cost_credits", "order")


class QuizQuestionInline(admin.TabularInline):
	model = QuizQuestion
	extra = 1
	fields = ("question", "order")
	autocomplete_fields = ("question",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
	fieldsets = (
		("Question placement", {"fields": ("topic", "concept", "difficulty")}),
		("Question content", {"fields": ("prompt", "explanation")}),
		("Scoring rules", {"fields": ("allow_multiple_answers", "marks", "negative_marks")}),
		("Publishing", {"fields": ("status", "published_at")}),
		("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)
	inlines = (OptionInline, HintInline)
	readonly_fields = ("created_at", "updated_at")
	list_display = ("short_prompt", "topic", "difficulty", "marks", "status", "updated_at")
	list_filter = ("status", "difficulty", "allow_multiple_answers", "topic__subject")
	search_fields = ("prompt", "explanation", "topic__title", "concept__title")
	autocomplete_fields = ("topic", "concept")
	list_select_related = ("topic", "concept")

	@admin.display(description="Prompt")
	def short_prompt(self, obj):
		return obj.prompt[:80]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
	fieldsets = (
		("Quiz placement", {"fields": ("topic", "title", "duration_seconds")}),
		("Publishing", {"fields": ("status", "published_at")}),
		("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)
	inlines = (QuizQuestionInline,)
	readonly_fields = ("public_id", "created_at", "updated_at")
	list_display = ("title", "topic", "question_count", "duration_seconds", "status", "updated_at")
	list_filter = ("status", "topic__subject", "topic__grade")
	search_fields = ("title", "topic__title")
	autocomplete_fields = ("topic",)
	list_select_related = ("topic",)

	@admin.display(description="Questions")
	def question_count(self, obj):
		return obj.questions.count()


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
	list_display = ("quiz", "question", "order")
	list_filter = ("quiz__topic__subject",)
	search_fields = ("quiz__title", "question__prompt")
	autocomplete_fields = ("quiz", "question")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
	fieldsets = (("Attempt", {"fields": ("student", "quiz", "status", "score")}), ("Timing", {"fields": ("started_at", "submitted_at")}))
	readonly_fields = ("public_id", "created_at", "updated_at", "started_at", "submitted_at")
	list_display = ("student", "quiz", "status", "score", "started_at", "submitted_at")
	list_filter = ("status", "quiz__topic__subject")
	search_fields = ("student__display_name", "student__user__username", "quiz__title")
	autocomplete_fields = ("student", "quiz")
	list_select_related = ("student", "quiz")


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
	fieldsets = (("Response", {"fields": ("attempt", "question", "selected_options")}), ("Result", {"fields": ("is_correct", "marks_awarded", "answered_at")}))
	readonly_fields = ("created_at", "updated_at")
	list_display = ("attempt", "question", "is_correct", "marks_awarded", "answered_at")
	list_filter = ("is_correct", "attempt__quiz__topic__subject")
	search_fields = ("attempt__student__display_name", "question__prompt")
	autocomplete_fields = ("attempt", "question", "selected_options")


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
	list_display = ("text", "question", "is_correct", "order")
	list_filter = ("is_correct", "question__difficulty")
	search_fields = ("text", "question__prompt")
	autocomplete_fields = ("question",)


@admin.register(Hint)
class HintAdmin(admin.ModelAdmin):
	list_display = ("question", "order", "cost_credits")
	list_filter = ("cost_credits", "question__difficulty")
	search_fields = ("text", "question__prompt")
	autocomplete_fields = ("question",)