from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from common.throttles import BurstRateThrottle, SustainedRateThrottle
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer


class PlanListView(ListAPIView):
    """GET /api/subscriptions/plans/ — all active plans (public)."""
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    queryset = Plan.objects.filter(is_active=True)


class MySubscriptionsView(ListAPIView):
    """GET /api/subscriptions/mine/ — current student's subscriptions."""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def get_queryset(self):
        if not hasattr(self.request.user, "student_profile"):
            return Subscription.objects.none()
        return (
            Subscription.objects.filter(student=self.request.user.student_profile)
            .select_related("plan")
            .order_by("-start_date")
        )
