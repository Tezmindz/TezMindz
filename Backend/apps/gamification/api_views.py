from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.throttles import BurstRateThrottle, SustainedRateThrottle
from .models import Badge, StudentBadge
from .serializers import BadgeSerializer, StudentBadgeSerializer


class BadgeListView(ListAPIView):
    """GET /api/gamification/badges/ — all active badges."""
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    queryset = Badge.objects.filter(is_active=True)


class StudentBadgeListView(ListAPIView):
    """GET /api/gamification/my-badges/ — current student's earned badges."""
    serializer_class = StudentBadgeSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def get_queryset(self):
        if not hasattr(self.request.user, "student_profile"):
            return StudentBadge.objects.none()
        return (
            StudentBadge.objects.filter(student=self.request.user.student_profile)
            .select_related("badge")
            .order_by("-earned_at")
        )
