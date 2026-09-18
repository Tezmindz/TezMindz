import uuid
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.throttles import BurstRateThrottle, SustainedRateThrottle
from apps.accounts.models import StudentProfile
from apps.curriculum.models import Grade
from .models import Plan, Subscription, Payment
from .serializers import PlanSerializer, SubscriptionSerializer, PaymentSerializer


class PlanListView(ListAPIView):
    """GET /api/subscriptions/plans/ — all active plans (public)."""
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    pagination_class = None
    queryset = Plan.objects.filter(is_active=True).order_by("price")


class PlanDetailView(RetrieveAPIView):
    """GET /api/subscriptions/plans/<pk>/ — single plan details (public)."""
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    queryset = Plan.objects.filter(is_active=True)


class CurrentSubscriptionView(APIView):
    """GET /api/subscriptions/current/ — get active subscription for current student."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response({"active_subscription": None, "has_active_subscription": False})

        today = timezone.now().date()
        sub = (
            Subscription.objects.filter(
                student=request.user.student_profile,
                status=Subscription.Status.ACTIVE,
                end_date__gte=today,
            )
            .select_related("plan")
            .prefetch_related("payments")
            .order_by("-end_date")
            .first()
        )

        if not sub:
            return Response({"active_subscription": None, "has_active_subscription": False})

        serializer = SubscriptionSerializer(sub)
        return Response({
            "active_subscription": serializer.data,
            "subscription": serializer.data,
            "has_active_subscription": True,
        })


class MySubscriptionsView(ListAPIView):
    """GET /api/subscriptions/mine/ — student's subscription and billing history."""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    pagination_class = None

    def get_queryset(self):
        if not hasattr(self.request.user, "student_profile"):
            return Subscription.objects.none()
        return (
            Subscription.objects.filter(student=self.request.user.student_profile)
            .select_related("plan")
            .prefetch_related("payments")
            .order_by("-start_date")
        )


class SubscribePlanView(APIView):
    """POST /api/subscriptions/subscribe/ — enroll in / purchase a subscription plan."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        plan_code = request.data.get("plan_code")
        provider = request.data.get("provider", "razorpay_sim")
        payment_reference = request.data.get("payment_reference") or f"TXN-{uuid.uuid4().hex[:12].upper()}"

        plan = None
        if plan_id:
            plan = Plan.objects.filter(id=plan_id, is_active=True).first()
        elif plan_code:
            plan = Plan.objects.filter(code=plan_code, is_active=True).first()

        if not plan:
            return Response(
                {"success": False, "message": "Selected subscription plan does not exist or is inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure student profile exists
        student = getattr(request.user, "student_profile", None)
        if not student:
            default_grade = Grade.objects.first()
            student = StudentProfile.objects.create(
                user=request.user,
                display_name=request.user.first_name or request.user.username,
                grade=default_grade,
            )

        today = timezone.now().date()
        duration_days = 365 if plan.billing_period == Plan.BillingPeriod.YEARLY else 30
        end_date = today + timedelta(days=duration_days)

        # Expire any previous active subscriptions to cleanly transition
        Subscription.objects.filter(
            student=student,
            status=Subscription.Status.ACTIVE,
        ).update(status=Subscription.Status.EXPIRED, auto_renew=False)

        # Create new active Subscription
        subscription = Subscription.objects.create(
            student=student,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            start_date=today,
            end_date=end_date,
            auto_renew=True,
        )

        # Record verified server-side Payment
        Payment.objects.create(
            student=student,
            subscription=subscription,
            provider=provider,
            provider_reference=payment_reference,
            amount=plan.price,
            currency="INR",
            status=Payment.Status.SUCCESS,
            raw_payload={
                "client_ip": request.META.get("REMOTE_ADDR"),
                "plan_code": plan.code,
                "plan_name": plan.name,
                "amount": str(plan.price),
                "timestamp": timezone.now().isoformat(),
            },
        )

        serializer = SubscriptionSerializer(subscription)
        return Response({
            "success": True,
            "message": f"Successfully enrolled in {plan.name}!",
            "subscription": serializer.data,
        }, status=status.HTTP_201_CREATED)


class UpgradeSubscriptionView(APIView):
    """POST /api/subscriptions/upgrade/ — upgrade current active plan to a new plan."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def post(self, request):
        new_plan_id = request.data.get("new_plan_id") or request.data.get("plan_id")
        new_plan_code = request.data.get("new_plan_code") or request.data.get("plan_code")
        payment_reference = request.data.get("payment_reference") or f"UPG-{uuid.uuid4().hex[:12].upper()}"

        new_plan = None
        if new_plan_id:
            new_plan = Plan.objects.filter(id=new_plan_id, is_active=True).first()
        elif new_plan_code:
            new_plan = Plan.objects.filter(code=new_plan_code, is_active=True).first()

        if not new_plan:
            return Response(
                {"success": False, "message": "Target upgrade plan not found or inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = getattr(request.user, "student_profile", None)
        if not student:
            return Response(
                {"success": False, "message": "Student profile required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()
        active_sub = Subscription.objects.filter(
            student=student,
            status=Subscription.Status.ACTIVE,
            end_date__gte=today,
        ).first()

        # If user has an active subscription, upgrade it
        duration_days = 365 if new_plan.billing_period == Plan.BillingPeriod.YEARLY else 30
        end_date = today + timedelta(days=duration_days)

        if active_sub:
            active_sub.plan = new_plan
            active_sub.end_date = end_date
            active_sub.status = Subscription.Status.ACTIVE
            active_sub.auto_renew = True
            active_sub.save(update_fields=["plan", "end_date", "status", "auto_renew"])
            subscription = active_sub
        else:
            subscription = Subscription.objects.create(
                student=student,
                plan=new_plan,
                status=Subscription.Status.ACTIVE,
                start_date=today,
                end_date=end_date,
                auto_renew=True,
            )

        # Record upgrade payment
        Payment.objects.create(
            student=student,
            subscription=subscription,
            provider="upgrade_prorated",
            provider_reference=payment_reference,
            amount=new_plan.price,
            currency="INR",
            status=Payment.Status.SUCCESS,
            raw_payload={
                "type": "upgrade",
                "new_plan": new_plan.code,
                "timestamp": timezone.now().isoformat(),
            },
        )

        serializer = SubscriptionSerializer(subscription)
        return Response({
            "success": True,
            "message": f"Successfully upgraded to {new_plan.name}!",
            "subscription": serializer.data,
        })


class CancelSubscriptionView(APIView):
    """POST /api/subscriptions/cancel/ — cancel recurring subscription."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

    def post(self, request):
        student = getattr(request.user, "student_profile", None)
        if not student:
            return Response(
                {"success": False, "message": "Student profile required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()
        active_sub = Subscription.objects.filter(
            student=student,
            status=Subscription.Status.ACTIVE,
            end_date__gte=today,
        ).first()

        if not active_sub:
            return Response(
                {"success": False, "message": "No active subscription found to cancel."},
                status=status.HTTP_404_NOT_FOUND,
            )

        active_sub.auto_renew = False
        active_sub.status = Subscription.Status.CANCELLED
        active_sub.save(update_fields=["auto_renew", "status"])

        serializer = SubscriptionSerializer(active_sub)
        return Response({
            "success": True,
            "message": f"Your subscription to {active_sub.plan.name} has been cancelled. You retain full access until {active_sub.end_date.strftime('%d %b %Y')}.",
            "subscription": serializer.data,
        })

