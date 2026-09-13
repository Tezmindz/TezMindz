from django.contrib import admin

from .models import Plan, Subscription, TrialGameLog, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
	fieldsets = (("Plan details", {"fields": ("code", "name", "price", "billing_period", "is_active")}), ("Included features", {"fields": ("features",)}))
	list_display = ("name", "code", "price", "billing_period", "is_active", "subscriber_count")
	list_filter = ("billing_period", "is_active")
	search_fields = ("name", "code")

	@admin.display(description="Subscribers")
	def subscriber_count(self, obj):
		return obj.subscriptions.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
	fieldsets = (("Subscriber", {"fields": ("student", "plan")}), ("Term", {"fields": ("status", "start_date", "end_date", "auto_renew")}))
	list_display = ("student", "plan", "status", "start_date", "end_date", "auto_renew")
	list_filter = ("status", "auto_renew", "plan")
	search_fields = ("student__display_name", "student__user__username", "plan__name")
	autocomplete_fields = ("student", "plan")
	list_select_related = ("student", "plan")


@admin.register(TrialGameLog)
class TrialGameLogAdmin(admin.ModelAdmin):
	fieldsets = (("Trial usage", {"fields": ("student", "game", "first_played_at")}),)
	readonly_fields = ("first_played_at",)
	list_display = ("student", "game", "first_played_at")
	list_filter = ("first_played_at", "game__game_type")
	search_fields = ("student__display_name", "student__user__username", "game__title")
	autocomplete_fields = ("student", "game")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	fieldsets = (("Payment", {"fields": ("student", "subscription", "provider", "provider_reference", "amount", "currency", "status")}), ("Provider audit", {"fields": ("raw_payload", "created_at")}))
	readonly_fields = ("created_at",)
	list_display = ("student", "amount", "currency", "provider", "status", "created_at")
	list_filter = ("status", "provider", "currency", "created_at")
	search_fields = ("student__display_name", "student__user__username", "provider_reference")
	autocomplete_fields = ("student", "subscription")
