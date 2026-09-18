from django.urls import path
from .api_views import (
    PlanListView,
    PlanDetailView,
    CurrentSubscriptionView,
    MySubscriptionsView,
    SubscribePlanView,
    UpgradeSubscriptionView,
    CancelSubscriptionView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("plans/<int:pk>/", PlanDetailView.as_view(), name="plan-detail"),
    path("current/", CurrentSubscriptionView.as_view(), name="subscription-current"),
    path("mine/", MySubscriptionsView.as_view(), name="my-subscriptions"),
    path("subscribe/", SubscribePlanView.as_view(), name="subscription-subscribe"),
    path("upgrade/", UpgradeSubscriptionView.as_view(), name="subscription-upgrade"),
    path("cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
]

