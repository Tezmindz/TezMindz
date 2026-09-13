from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	fieldsets = (("Event", {"fields": ("student", "event_type", "payload", "created_at")}),)
	readonly_fields = ("created_at",)
	list_display = ("event_type", "student", "created_at")
	list_filter = ("event_type", "created_at")
	search_fields = ("student__display_name", "student__user__username")
	autocomplete_fields = ("student",)
	list_select_related = ("student",)
