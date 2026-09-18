from django.utils import timezone
from rest_framework import serializers
from .models import Plan, Subscription, Payment


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "code", "name", "price", "billing_period", "features", "is_active"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "provider",
            "provider_reference",
            "amount",
            "currency",
            "status",
            "created_at",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_code = serializers.CharField(source="plan.code", read_only=True)
    plan_price = serializers.DecimalField(source="plan.price", max_digits=8, decimal_places=2, read_only=True)
    plan_billing_period = serializers.CharField(source="plan.billing_period", read_only=True)
    plan_features = serializers.JSONField(source="plan.features", read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_active_entitled = serializers.SerializerMethodField()
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "plan_code",
            "plan_name",
            "plan_price",
            "plan_billing_period",
            "plan_features",
            "status",
            "start_date",
            "end_date",
            "auto_renew",
            "days_remaining",
            "is_active_entitled",
            "payments",
        ]

    def get_days_remaining(self, obj):
        if not obj.end_date:
            return 0
        today = timezone.now().date()
        diff = (obj.end_date - today).days
        return max(0, diff)

    def get_is_active_entitled(self, obj):
        today = timezone.now().date()
        return obj.status == Subscription.Status.ACTIVE and obj.end_date >= today

