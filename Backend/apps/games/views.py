from django.shortcuts import get_object_or_404, render, redirect

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.subscriptions.services import can_student_access_game
from common.throttles import BurstRateThrottle, SustainedRateThrottle

from .models import Game
from .serializers import GameSerializer


class GameDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def get(self, request, public_id):
        game = get_object_or_404(
            Game.published,
            public_id=public_id,
        )

        if not can_student_access_game(
            request.user.student_profile,
            game,
        ):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "ACCESS_DENIED",
                        "message": "You do not have access to this game.",
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GameSerializer(game)

        return Response(
            {
                "success": True,
                "data": serializer.data,
            }
        )


def dream_house_builder_view(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/games/dream-house-builder/")
    # Existing game page — we'll fix its lookup separately.
    game = Game.objects.first()

    return render(
        request,
        "games/game_player.html",
        {"game": game},
    )