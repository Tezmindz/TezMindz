from django.contrib import admin

from .models import TopicProgress


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
	fieldsets = (
		("Learner and mission", {"fields": ("student", "topic")}),
		("Mastery progress", {"fields": ("attempts", "correct_count", "incorrect_count", "best_score", "last_activity_at")}),
	)
	readonly_fields = ("last_activity_at",)
	list_display = ("student", "topic", "attempts", "accuracy_display", "best_score", "last_activity_at")
	list_filter = ("topic__subject", "topic__grade", "last_activity_at")
	search_fields = ("student__display_name", "student__user__username", "topic__title")
	autocomplete_fields = ("student", "topic")
	list_select_related = ("student", "topic")

	@admin.display(description="Accuracy")
	def accuracy_display(self, obj):
		return obj.accuracy
