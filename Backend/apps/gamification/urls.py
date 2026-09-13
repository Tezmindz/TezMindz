from django.urls import path
from .api_views import BadgeListView, StudentBadgeListView

urlpatterns = [
    path("badges/", BadgeListView.as_view(), name="badge-list"),
    path("my-badges/", StudentBadgeListView.as_view(), name="student-badge-list"),
]
