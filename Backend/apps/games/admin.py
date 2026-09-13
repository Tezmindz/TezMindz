from django.contrib import admin

from .models import Game, GameSession, GameContent
from .admin_forms import GameAdminForm


class GameContentInline(admin.TabularInline):
	model = GameContent
	extra = 1
	fields = ("order", "prompt", "content_type", "points", "data", "correct_answer", "hints")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
	form = GameAdminForm
	inlines = [GameContentInline]
	fieldsets = (
		("Curriculum placement", {"fields": ("grade", "subject", "chapter", "concept")}),
		("Game details", {"fields": ("title", "description", "game_type")}),
		("Difficulty and access", {"fields": ("difficulty", "access_tier")}),
		("Playable configuration (legacy / global JSON)", {"fields": ("config",), "classes": ("collapse",)}),
		("Publishing", {"fields": ("status", "published_at")}),
		("System identity", {"fields": ("public_id", "created_at", "updated_at"), "classes": ("collapse",)}),
	)
	readonly_fields = ("public_id", "created_at", "updated_at")
	list_display = ("title", "game_type", "concept", "difficulty", "access_tier", "status", "updated_at")
	list_filter = ("status", "game_type", "difficulty", "access_tier", "concept__topic__subject", "concept__topic__grade")
	search_fields = ("title", "description", "concept__title", "concept__topic__title", "concept__topic__subject__name")
	list_select_related = ("concept", "concept__topic", "concept__topic__subject", "concept__topic__grade")

	class Media:
		js = ("admin/js/curriculum_dependent_selects.js",)



@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
	fieldsets = (
		("Play session", {"fields": ("student", "game", "level", "status")}),
		("Performance", {"fields": ("score", "accuracy", "time_spent_seconds", "correct_actions", "wrong_actions")}),
		("Reward and payload", {"fields": ("reward_granted", "client_result_payload")}),
		("Timing", {"fields": ("started_at", "completed_at", "created_at", "updated_at"), "classes": ("collapse",)}),
	)
	readonly_fields = ("public_id", "started_at", "completed_at", "created_at", "updated_at")
	list_display = ("student", "game", "level", "status", "score", "accuracy", "reward_granted", "started_at")
	list_filter = ("status", "reward_granted", "game__game_type", "game__difficulty")
	search_fields = ("student__display_name", "student__user__username", "game__title")
	autocomplete_fields = ("student", "game")
	list_select_related = ("student", "game")
