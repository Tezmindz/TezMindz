from django.contrib import admin

from apps.games.models import Game

from .models import Concept, Grade, LearningWorld, Subject, Topic

@admin.register(LearningWorld)
class LearningWorldAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'is_active')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
	fieldsets = (("Grade identity", {"fields": ("name", "order")}),)
	list_display = ("name", "order", "topic_count", "created_at")
	search_fields = ("name",)
	ordering = ("order",)

	@admin.display(description="Topics")
	def topic_count(self, obj):
		return obj.topics.count()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
	fieldsets = (("Learning world", {"fields": ("name", "slug", "order")}),)
	list_display = ("name", "slug", "order", "topic_count", "updated_at")
	search_fields = ("name", "slug")
	ordering = ("order", "name")

	@admin.display(description="Topics")
	def topic_count(self, obj):
		return obj.topics.count()


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
	fieldsets = (
		("Learning world", {"fields": ("grade", "subject", "title", "order", "difficulty")}),
		("Mission content", {"fields": ("description", "learning_objectives", "estimated_minutes")}),
		("Unlocking and publishing", {"fields": ("prerequisites", "status", "published_at")}),
		("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)
	readonly_fields = ("created_at", "updated_at")
	list_display = ("title", "grade", "subject", "difficulty", "status", "order", "updated_at")
	list_filter = ("status", "difficulty", "grade", "subject")
	search_fields = ("title", "description", "learning_objectives")
	autocomplete_fields = ("grade", "subject", "prerequisites")
	list_select_related = ("grade", "subject")
	ordering = ("grade__order", "subject__order", "order")


from .admin_forms import ConceptAdminForm


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
	form = ConceptAdminForm
	fieldsets = (
		("Curriculum placement", {"fields": ("grade", "subject", "topic")}),
		("Mission details", {"fields": ("title", "order")}),
		("Learn content", {"fields": ("content_body",)}),
		("Publishing", {"fields": ("status", "published_at")}),
		("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)
	readonly_fields = ("created_at", "updated_at")
	list_display = ("title", "topic", "order", "status", "updated_at")
	list_filter = ("status", "topic__subject", "topic__grade")
	search_fields = ("title", "content_body", "topic__title")
	list_select_related = ("topic", "topic__grade", "topic__subject")
	ordering = ("topic", "order")

	class Media:
		js = ("admin/js/curriculum_dependent_selects.js",)

