from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.throttles import BurstRateThrottle, SustainedRateThrottle
from .models import TopicProgress
from .serializers import TopicProgressSerializer


class TopicProgressListView(ListAPIView):
    """GET /api/progress/ — current student's topic progress."""

    serializer_class = TopicProgressSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def get_queryset(self):
        if not hasattr(self.request.user, "student_profile"):
            return TopicProgress.objects.none()
        return (
            TopicProgress.objects.filter(student=self.request.user.student_profile)
            .select_related("topic", "topic__subject", "topic__grade")
            .order_by("-last_activity_at")
        )
