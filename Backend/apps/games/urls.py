from django.urls import path

from .views import (
    dream_house_builder_view,
    GameDetailAPIView,
)

urlpatterns = [
    path(
        "dream-house-builder/",
        dream_house_builder_view,
        name="dream-house-builder",
    ),

    path(
        "api/<uuid:public_id>/",
        GameDetailAPIView.as_view(),
        name="game-detail-api",
    ),
]