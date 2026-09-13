from django.urls import path
from .views import DemoLoginView
from .api_views import StudentMeView, ForgotPasswordRequestView, ForgotPasswordVerifyView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("demo-login/", DemoLoginView.as_view(), name="demo-login"),
    path("me/", StudentMeView.as_view(), name="student-me"),
    path("forgot-password/", ForgotPasswordRequestView.as_view(), name="forgot_password_request"),
    path("forgot-password/verify/", ForgotPasswordVerifyView.as_view(), name="forgot_password_verify"),
    path("jwt/create/", TokenObtainPairView.as_view(), name="jwt-create"),
    path("jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
]