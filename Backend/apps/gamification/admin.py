from django.contrib import admin
from .models import CreditAccount, CreditTransaction, XPAccount, XPLevelThreshold, XPTransaction, Badge, StudentBadge, DailyChallenge

@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "active_date", "is_published", "xp_reward", "coin_reward")
    list_filter = ("active_date", "is_published")
    search_fields = ("title", "description")



@admin.register(CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
	fieldsets = (("Learner wallet", {"fields": ("student", "balance")}),)
	list_display = ("student", "balance", "transaction_count")
	list_filter = ("balance",)
	search_fields = ("student__display_name", "student__user__username")
	autocomplete_fields = ("student",)

	@admin.display(description="Transactions")
	def transaction_count(self, obj):
		return obj.transactions.count()


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
	fieldsets = (("Wallet transaction", {"fields": ("account", "amount", "transaction_type", "reference", "description")}), ("Audit", {"fields": ("created_at",)}))
	readonly_fields = ("created_at",)
	list_display = ("account", "amount", "transaction_type", "reference", "created_at")
	list_filter = ("transaction_type", "created_at")
	search_fields = ("account__student__display_name", "account__student__user__username", "reference", "description")
	autocomplete_fields = ("account",)


@admin.register(XPAccount)
class XPAccountAdmin(admin.ModelAdmin):
	fieldsets = (("Learner progression", {"fields": ("student", "total_xp", "current_level")}),)
	list_display = ("student", "current_level", "total_xp", "transaction_count")
	list_filter = ("current_level",)
	search_fields = ("student__display_name", "student__user__username")
	autocomplete_fields = ("student",)

	@admin.display(description="Transactions")
	def transaction_count(self, obj):
		return obj.transactions.count()


@admin.register(XPLevelThreshold)
class XPLevelThresholdAdmin(admin.ModelAdmin):
	fieldsets = (("Level curve", {"fields": ("level", "xp_required")}),)
	list_display = ("level", "xp_required")
	search_fields = ("level",)
	ordering = ("level",)


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
	fieldsets = (("XP event", {"fields": ("account", "amount", "source", "reference", "description")}), ("Audit", {"fields": ("created_at",)}))
	readonly_fields = ("created_at",)
	list_display = ("account", "amount", "source", "reference", "created_at")
	list_filter = ("source", "created_at")
	search_fields = ("account__student__display_name", "account__student__user__username", "reference", "description")
	autocomplete_fields = ("account",)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
	fieldsets = (("Badge identity", {"fields": ("code", "name", "description", "icon_key", "is_active")}), ("Unlock criteria", {"fields": ("criteria",)}))
	list_display = ("name", "code", "icon_key", "is_active", "awarded_count")
	list_filter = ("is_active",)
	search_fields = ("name", "code", "description")

	@admin.display(description="Awarded")
	def awarded_count(self, obj):
		return obj.awarded_to.count()


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
	fieldsets = (("Achievement", {"fields": ("student", "badge")}), ("Award audit", {"fields": ("earned_at",)}))
	readonly_fields = ("earned_at",)
	list_display = ("student", "badge", "earned_at")
	list_filter = ("badge", "earned_at")
	search_fields = ("student__display_name", "student__user__username", "badge__name")
	autocomplete_fields = ("student", "badge")
