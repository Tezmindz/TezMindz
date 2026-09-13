from django.urls import path
from .api import submit_quiz_attempt

urlpatterns = [
    path("submit/", submit_quiz_attempt, name="submit_quiz_attempt"),
]
