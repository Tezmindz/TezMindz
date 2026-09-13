from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.throttles import BurstRateThrottle, SustainedRateThrottle
from .serializers import UserMeSerializer, StudentProfileSerializer


class StudentMeView(APIView):
    """GET/PATCH /api/auth/me/ — current user + student profile."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = UserMeSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if hasattr(user, "student_profile") and "student_profile" in request.data:
            profile_data = request.data["student_profile"]
            profile_serializer = StudentProfileSerializer(
                user.student_profile, data=profile_data, partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return Response(UserMeSerializer(user).data)


import random
import string
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny
from .models import OTPVerification, User

class ForgotPasswordRequestView(APIView):
    """POST /api/auth/forgot-password/"""
    permission_classes = [AllowAny]
    throttle_classes = [BurstRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"success": False, "message": "Email required."}, status=400)
            
        user = User.objects.filter(email=email).first()
        if not user:
            # Do not reveal if email exists, just return success
            return Response({"success": True, "message": "If an account exists, an OTP has been sent."})
            
        # Check rate limit (max 3 unused OTPs in last hour)
        recent_otps = OTPVerification.objects.filter(
            user=user, 
            created_at__gte=timezone.now() - timedelta(hours=1),
            is_used=False
        ).count()
        if recent_otps >= 3:
            return Response({"success": False, "message": "Too many requests. Please try again later."}, status=429)

        # Generate secure OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        
        # Save hash
        OTPVerification.objects.create(
            user=user,
            otp_hash=make_password(otp_code),
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        # Send email
        try:
            send_mail(
                subject="Tezz-Mindz Password Reset OTP",
                message=f"Your OTP for password reset is: {otp_code}\nThis OTP is valid for 15 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass # In dev, fail_silently avoids crashing if SMTP is missing
            
        return Response({"success": True, "message": "If an account exists, an OTP has been sent."})


class ForgotPasswordVerifyView(APIView):
    """POST /api/auth/forgot-password/verify/"""
    permission_classes = [AllowAny]
    throttle_classes = [BurstRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        otp_code = request.data.get("otp", "").strip()
        new_password = request.data.get("new_password", "")
        
        if not email or not otp_code or not new_password:
            return Response({"success": False, "message": "Missing fields."}, status=400)
            
        if len(new_password) < 6:
            return Response({"success": False, "message": "Password must be at least 6 characters."}, status=400)
            
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"success": False, "message": "Invalid OTP."}, status=400)
            
        # Get latest unused unexpired OTP
        otp_obj = OTPVerification.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()
        
        if not otp_obj:
            return Response({"success": False, "message": "Invalid or expired OTP."}, status=400)
            
        if otp_obj.attempts >= 5:
            otp_obj.is_used = True
            otp_obj.save(update_fields=['is_used'])
            return Response({"success": False, "message": "Too many failed attempts. Request a new OTP."}, status=400)
            
        from django.contrib.auth.hashers import check_password
        if not check_password(otp_code, otp_obj.otp_hash):
            otp_obj.attempts += 1
            otp_obj.save(update_fields=['attempts'])
            return Response({"success": False, "message": "Invalid OTP."}, status=400)
            
        # Success
        otp_obj.is_used = True
        otp_obj.save(update_fields=['is_used'])
        
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        return Response({"success": True, "message": "Password updated successfully."})
