from django.contrib import admin

from .models import (
	Hint, Option, Question, QuestionResponse, Quiz, QuizAttempt, QuizQuestion,
	MockTest, MockTestQuestion, MockTestAttempt, MockTestResponse
)


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


class MockTestQuestionInline(admin.TabularInline):
	model = MockTestQuestion
	extra = 1
	fields = ("question", "order")
	autocomplete_fields = ("question",)


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
	fieldsets = (
		("Test Info", {"fields": ("title", "description", "grade", "subject")}),
		("Configuration", {"fields": ("duration_seconds", "passing_percentage", "order")}),
		("Publishing", {"fields": ("status", "published_at")}),
		("System Dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)
	inlines = (MockTestQuestionInline,)
	readonly_fields = ("public_id", "created_at", "updated_at")
	list_display = ("title", "grade", "subject", "question_count", "duration_minutes", "total_marks_display", "status", "updated_at")
	list_filter = ("status", "grade", "subject")
	search_fields = ("title", "description")
	autocomplete_fields = ("grade", "subject")
	actions = ["publish_tests", "unpublish_tests"]

	@admin.display(description="Questions")
	def question_count(self, obj):
		return obj.questions.count()

	@admin.display(description="Total Marks")
	def total_marks_display(self, obj):
		return obj.computed_total_marks

	@admin.action(description="Publish selected Mock Tests")
	def publish_tests(self, request, queryset):
		from django.utils import timezone
		from django.contrib import messages
		published_count = 0
		errors = []
		for test in queryset:
			count = test.questions.count()
			if count == 0:
				errors.append(f"'{test.title}' cannot be published: It has no questions assigned.")
				continue
			mismatched = test.questions.exclude(topic__grade=test.grade)
			if mismatched.exists():
				errors.append(f"'{test.title}' contains {mismatched.count()} questions that do not belong to Grade '{test.grade.name}'.")
				continue
			test.status = "published"
			test.published_at = timezone.now()
			test.save(update_fields=["status", "published_at", "updated_at"])
			published_count += 1

		if published_count:
			self.message_user(request, f"Successfully published {published_count} Mock Test(s).")
		if errors:
			for err in errors:
				self.message_user(request, err, level=messages.ERROR)

	@admin.action(description="Unpublish selected Mock Tests")
	def unpublish_tests(self, request, queryset):
		queryset.update(status="draft")
		self.message_user(request, f"Unpublished {queryset.count()} Mock Test(s).")


@admin.register(MockTestQuestion)
class MockTestQuestionAdmin(admin.ModelAdmin):
	list_display = ("mock_test", "question", "order")
	list_filter = ("mock_test__grade", "mock_test__subject")
	search_fields = ("mock_test__title", "question__prompt")
	autocomplete_fields = ("mock_test", "question")


@admin.register(MockTestAttempt)
class MockTestAttemptAdmin(admin.ModelAdmin):
	fieldsets = (
		("Attempt Details", {"fields": ("student", "mock_test", "status", "score", "total_marks", "percentage")}),
		("Timing", {"fields": ("started_at", "submitted_at")}),
	)
	readonly_fields = ("public_id", "created_at", "updated_at", "started_at", "submitted_at")
	list_display = ("student", "mock_test", "status", "score", "total_marks", "percentage", "started_at", "submitted_at")
	list_filter = ("status", "mock_test__grade", "mock_test__subject")
	search_fields = ("student__display_name", "student__user__username", "mock_test__title")
	autocomplete_fields = ("student", "mock_test")
	list_select_related = ("student", "mock_test")


@admin.register(MockTestResponse)
class MockTestResponseAdmin(admin.ModelAdmin):
	readonly_fields = ("created_at", "updated_at")
	list_display = ("attempt", "question", "is_correct", "marks_awarded", "answered_at")
	list_filter = ("is_correct", "attempt__mock_test__grade")
	search_fields = ("attempt__student__display_name", "question__prompt")
	autocomplete_fields = ("attempt", "question", "selected_options")