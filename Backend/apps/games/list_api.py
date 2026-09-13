from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from common.throttles import BurstRateThrottle, SustainedRateThrottle
from .models import Game
from .serializers import GameSerializer


class GameListAPIView(ListAPIView):
    """GET /api/games/list/ — browse published games with filtering."""

    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["game_type", "difficulty", "access_tier"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]
    ordering = ["title"]

    def get_queryset(self):
        qs = Game.published.all().select_related(
            "concept", "concept__topic", "concept__topic__subject", "concept__topic__grade"
        )
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            qs = qs.filter(concept__topic_id=topic_id)
        subject_id = self.request.query_params.get("subject")
        if subject_id:
            qs = qs.filter(concept__topic__subject_id=subject_id)
        grade_id = self.request.query_params.get("grade")
        if grade_id:
            qs = qs.filter(concept__topic__grade_id=grade_id)
        return qs
