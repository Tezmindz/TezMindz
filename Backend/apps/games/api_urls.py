from django.urls import path
from .api import start_game_session, submit_game_session, submit_game_direct, plugins_list_api
from .list_api import GameListAPIView

urlpatterns = [
    path("list/", GameListAPIView.as_view(), name="game-list"),
    path("plugins/", plugins_list_api, name="game-plugins-list"),
    path("<int:game_id>/start/", start_game_session, name="start_session"),
    path("sessions/<str:session_id>/submit/", submit_game_session, name="submit_session"),
    path("submit/", submit_game_direct, name="submit_direct"),
]
