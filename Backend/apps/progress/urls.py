from django.urls import path
from .api_views import TopicProgressListView

urlpatterns = [
    path("", TopicProgressListView.as_view(), name="progress-list"),
]
