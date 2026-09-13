import json

from apps.subscriptions.services import can_student_access_game
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.throttles import GameSubmitThrottle
from .models import Game, GameSession
from .plugins import discover_game_plugins
from apps.progress.models import TopicProgress


def _check_throttle(request, throttle_cls):
    """
    Apply a DRF throttle class to a function-based API view.
    """
    throttle = throttle_cls()

    if not hasattr(request, "auth"):
        request.auth = None

    if not throttle.allow_request(request, view=None):
        wait = throttle.wait()
        response = JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "THROTTLED",
                    "message": "Too many requests. Please slow down.",
                },
            },
            status=429,
        )

        if wait is not None:
            response["Retry-After"] = str(int(wait))

        return response

    return None


@api_view(["POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def start_game_session(request, game_id):
    throttle_response = _check_throttle(request, GameSubmitThrottle)

    if throttle_response:
        return throttle_response

    if not hasattr(request.user, "student_profile"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "STUDENT_PROFILE_REQUIRED",
                    "message": "Not authenticated as a student.",
                },
            },
            status=403,
        )

    # Only published games can be started.
    game = get_object_or_404(
        Game.published,
        id=game_id,
    )

    student = request.user.student_profile

    if not can_student_access_game(student, game):
        return JsonResponse(
            {
                "success": False,
                "error": {
                "code": "ACCESS_DENIED",
                "message": "You do not have access to this game.",
            },
        },
        status=403,
    )


    session = GameSession.objects.create(
        student=student,
        game=game,
        status=GameSession.Status.IN_PROGRESS,
    )

    questions_payload = []
    for gc in game.contents.all().order_by("order"):
        questions_payload.append({
            "id": gc.id,
            "order": gc.order,
            "prompt": gc.prompt,
            "content_type": gc.content_type,
            "data": gc.data,
            "points": gc.points,
            "hints": gc.hints,
        })

    return JsonResponse(
        {
            "success": True,
            "session_id": str(session.id),
            "config": game.config,
            "questions": questions_payload,
        }
    )


@api_view(["POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def submit_game_session(request, session_id):
    throttle_response = _check_throttle(request, GameSubmitThrottle)

    if throttle_response:
        return throttle_response

    if not hasattr(request.user, "student_profile"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "STUDENT_PROFILE_REQUIRED",
                    "message": "Not authenticated as a student.",
                },
            },
            status=403,
        )

    try:
        payload = request.data
    except Exception:
        return JsonResponse({"success": False, "error": {"code": "INVALID_JSON", "message": "Invalid JSON."}}, status=400)

    student = request.user.student_profile
    
    with transaction.atomic():
        import uuid
        session = None
        if isinstance(session_id, int) or (isinstance(session_id, str) and session_id.isdigit()):
            session = GameSession.objects.select_for_update().filter(
                id=int(session_id), student=student, status=GameSession.Status.IN_PROGRESS
            ).first()
        if not session:
            try:
                val_uuid = uuid.UUID(str(session_id))
                session = GameSession.objects.select_for_update().filter(
                    public_id=val_uuid, student=student, status=GameSession.Status.IN_PROGRESS
                ).first()
            except (ValueError, TypeError):
                pass

        if not session:
            return JsonResponse({"success": False, "error": {"code": "SESSION_NOT_FOUND", "message": "Active session not found."}}, status=404)

        game = session.game
        config = game.config or {}
        levels = config.get("levels", [])

        # Generic Payload Handling
        level_id = payload.get("level_id")
        answer = payload.get("answer")
        time_spent = int(payload.get("time_taken", 0) or payload.get("time_spent", 0))

        # 1. Authoritative Validation
        is_correct = False
        awarded_xp = 0
        awarded_coins = 0
        points_earned = 0
        
        # Try to find the matching level config for validation
        current_level_config = None
        for lvl in levels:
            if str(lvl.get("id")) == str(level_id):
                current_level_config = lvl
                break

        if current_level_config:
            correct_answer = current_level_config.get("correct_answer")
            if correct_answer and answer:
                # Basic validation: compare answer dict/value with correct_answer dict/value
                # Example: answer = {"value": "123"}, correct_answer = {"value": "123"}
                # Or handle array order equality if present
                if isinstance(correct_answer, dict) and isinstance(answer, dict):
                    if "value" in correct_answer and "value" in answer:
                        is_correct = str(correct_answer["value"]) == str(answer["value"])
                    elif "order" in correct_answer and "order" in answer:
                        is_correct = correct_answer["order"] == answer["order"]
                else:
                    is_correct = str(answer) == str(correct_answer)
                
                if is_correct:
                    awarded_xp = current_level_config.get("reward_xp", 15)
                    awarded_coins = current_level_config.get("reward_coins", 5)
                    points_earned = awarded_xp  # Expose to frontend
            else:
                # If no strict correct_answer is defined in config, fallback to trusting client for soft-validation
                # This is the tradeoff documented for subjective/creative games
                is_correct = payload.get("is_correct", True)
                if is_correct:
                    awarded_xp = current_level_config.get("reward_xp", 15)
                    awarded_coins = current_level_config.get("reward_coins", 5)
                    points_earned = awarded_xp
        else:
            # Fallback if level is missing from config
            is_correct = payload.get("is_correct", True)
            if is_correct:
                awarded_xp = 15
                awarded_coins = 5
                points_earned = awarded_xp

        # 2. Update Session State
        # If the frontend passes a final score, we accumulate it or store it.
        # Here we just accumulate points.
        if is_correct:
            session.score = (session.score or 0) + points_earned
            session.correct_actions = (session.correct_actions or 0) + 1
        else:
            session.wrong_actions = (session.wrong_actions or 0) + 1

        session.time_spent_seconds = (session.time_spent_seconds or 0) + time_spent
        session.client_result_payload = payload
        
        # 3. Secure Reward Grant via Ledger (Phase 8 gamification integration)
        from apps.gamification.models import XPTransaction
        
        if is_correct:
            # We grant XP securely through the student profile (which wraps the logic)
            student.xp_points += awarded_xp
            student.adventure_coins += awarded_coins
            student.save(update_fields=["xp_points", "adventure_coins"])
            
            # Record securely in ledger
            # (Assuming XPAccount exists, we find or create it for ledgering)
            from apps.gamification.models import XPAccount
            xp_account, _ = XPAccount.objects.get_or_create(student=student)
            XPTransaction.objects.create(
                account=xp_account,
                amount=awarded_xp,
                source=XPTransaction.Source.GAME,
                reference=f"game_session_{session.id}_level_{level_id}"
            )
            
        session.save()

        # Update Topic Progress
        if game.concept and game.concept.topic:
            tp, created = TopicProgress.objects.get_or_create(student=student, topic=game.concept.topic)
            tp.attempts += 1
            if session.score > tp.best_score:
                tp.best_score = session.score
            tp.last_activity_at = timezone.now()
            tp.save()

    return JsonResponse({
        "success": True,
        "is_correct": is_correct,
        "current_score": session.score,
        "points_earned": points_earned,
        "xp_awarded": awarded_xp,
        "coins_awarded": awarded_coins,
        "total_xp": student.xp_points,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_game_direct(request):
    """
    Direct submit endpoint used by game players without pre-initialized session.
    Automatically creates completed session, evaluates score, grants rewards, and updates TopicProgress.
    """
    throttle_response = _check_throttle(request, GameSubmitThrottle)
    if throttle_response:
        return throttle_response

    student = None
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
    elif hasattr(request, 'auth') and hasattr(request.auth, 'user') and hasattr(request.auth.user, 'student_profile'):
        student = request.auth.user.student_profile

    if not student:
        return JsonResponse({"success": False, "error": {"code": "STUDENT_PROFILE_REQUIRED", "message": "Not authenticated as a student."}}, status=403)

    try:
        payload = request.data if hasattr(request, 'data') else json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": {"code": "INVALID_JSON", "message": "Invalid JSON."}}, status=400)

    game_id = payload.get("game_id")
    game = get_object_or_404(Game.published, id=game_id)

    score = int(payload.get("score", 100))
    time_spent = int(payload.get("time_spent", 0))
    is_correct = payload.get("is_correct", score > 0)

    awarded_xp = 15
    awarded_coins = 5
    if is_correct:
        config = game.config or {}
        levels = config.get("levels", [])
        if levels and isinstance(levels, list):
            awarded_xp = levels[0].get("reward_xp", 15)
            awarded_coins = levels[0].get("reward_coins", 5)

    with transaction.atomic():
        session = GameSession.objects.create(
            student=student,
            game=game,
            status=GameSession.Status.COMPLETED,
            score=score,
            accuracy=1.0 if is_correct else 0.0,
            time_spent_seconds=time_spent,
            client_result_payload=payload,
            reward_granted=is_correct,
            completed_at=timezone.now()
        )

        if is_correct:
            student.xp_points += awarded_xp
            student.adventure_coins += awarded_coins
            student.save(update_fields=["xp_points", "adventure_coins"])

            from apps.gamification.models import XPAccount, XPTransaction
            xp_account, _ = XPAccount.objects.get_or_create(student=student)
            XPTransaction.objects.create(
                account=xp_account,
                amount=awarded_xp,
                source=XPTransaction.Source.GAME,
                reference=f"game_session_{session.id}_direct"
            )

        if game.concept and game.concept.topic:
            tp, _ = TopicProgress.objects.get_or_create(student=student, topic=game.concept.topic)
            tp.attempts += 1
            if session.score > tp.best_score:
                tp.best_score = session.score
            tp.last_activity_at = timezone.now()
            tp.save()

    return JsonResponse({
        "success": True,
        "is_correct": is_correct,
        "current_score": score,
        "points_earned": awarded_xp,
        "xp_awarded": awarded_xp,
        "coins_awarded": awarded_coins,
        "total_xp": student.xp_points,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def plugins_list_api(request):
    """
    Returns the discovered game plugin manifests.
    """
    plugins = discover_game_plugins()
    return JsonResponse({"success": True, "plugins": plugins})