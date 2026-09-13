from django.urls import path

from . import views

app_name = "common"

urlpatterns = [
    path("", views.template_page("index.html"), name="home"),
    path("dashboard/", views.dashboard_page, name="dashboard"),
    path("login/", views.login_page, name="login"),
    path("tezadmin/", views.tezadmin_hub_page, name="tezadmin_hub"),
    path("tezadmin/login/", views.tezadmin_login_api_view, name="tezadmin_login"),
    path("register/", views.register_page, name="register"),
    path("logout/", views.logout_page, name="logout"),
    path("learn/", views.learn_page, name="learn"),
    path("games/", views.games_page, name="games"),
    path("progress/", views.progress_page, name="progress"),
    path("achievements/", views.achievements_page, name="achievements"),
    path("leaderboard/", views.leaderboard_page, name="leaderboard"),
    path("rewards/", views.rewards_page, name="rewards"),
    path("profile/", views.profile_page, name="profile"),
    path("class/", views.class_page, name="class"),
    path("world/<int:world_id>/", views.world_detail_page, name="world_detail"),
    path("subject/<int:subject_id>/", views.subject_page, name="subject"),
    path("chapter/<int:chapter_id>/", views.chapter_page, name="chapter"),
    path("concept/<int:concept_id>/", views.concept_page, name="concept"),
    path("quiz/<int:quiz_id>/", views.quiz_page, name="quiz"),
    path("quiz/result/<uuid:attempt_id>/", views.quiz_result_page, name="quiz_result"),
    path("game/<int:game_id>/difficulty/", views.game_difficulty_page, name="difficulty"),
    path("game/<int:game_id>/play/", views.game_play_page, name="game_play"),
    path("result/", views.template_page("result.html"), name="result"),
]
