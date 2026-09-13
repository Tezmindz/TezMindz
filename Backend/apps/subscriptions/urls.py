from django.urls import path
from .api_views import PlanListView, MySubscriptionsView

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("mine/", MySubscriptionsView.as_view(), name="my-subscriptions"),
]
