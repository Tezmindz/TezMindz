from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import MentorProfile, ParentProfile, StudentProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	fieldsets = (
		("Account", {"fields": ("username", "password")}),
		("Identity", {"fields": ("first_name", "last_name", "email", "role")}),
		("Access", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Activity", {"fields": ("last_login", "date_joined")}),
	)
	add_fieldsets = (
		("Create account", {"classes": ("wide",), "fields": ("username", "email", "password1", "password2", "role")}),
	)
	list_display = ("username", "email", "first_name", "role", "is_active", "is_staff", "date_joined")
	list_filter = ("role", "is_active", "is_staff", "date_joined")
	search_fields = ("username", "email", "first_name", "last_name")
	ordering = ("-date_joined",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
	fieldsets = (
		("Learner identity", {"fields": ("user", "display_name", "avatar_key")}),
		("Learning placement", {"fields": ("grade", "parent", "account_status")}),
		("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
	)
	readonly_fields = ("created_at", "updated_at")
	list_display = ("display_name", "user", "grade", "account_status", "created_at")
	list_filter = ("grade", "account_status", "avatar_key")
	search_fields = ("display_name", "user__username", "user__email")
	autocomplete_fields = ("user", "grade", "parent")
	list_select_related = ("user", "grade", "parent")


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
	fieldsets = (("Parent account", {"fields": ("user",)}), ("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}))
	readonly_fields = ("created_at", "updated_at")
	list_display = ("user", "children_count", "created_at")
	search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
	autocomplete_fields = ("user",)

	@admin.display(description="Children")
	def children_count(self, obj):
		return obj.children.count()


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
	fieldsets = (("Mentor account", {"fields": ("user", "assigned_subjects")} ), ("System dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}))
	readonly_fields = ("created_at", "updated_at")
	list_display = ("user", "subject_count", "created_at")
	search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
	autocomplete_fields = ("user", "assigned_subjects")

	@admin.display(description="Subjects")
	def subject_count(self, obj):
		return obj.assigned_subjects.count()
