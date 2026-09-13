import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.db import transaction

from common.throttles import QuizSubmitThrottle
from .models import Quiz, QuizAttempt, QuestionResponse, Question, Option
from apps.progress.models import TopicProgress


def _check_throttle(request, throttle_cls):
    """
    Apply a single DRF throttle class to a plain Django function view.
    Returns a 429 JsonResponse if the throttle limit is exceeded,
    or None if the request is allowed through.
    """
    throttle = throttle_cls()
    if not hasattr(request, 'auth'):
        request.auth = None
    if not throttle.allow_request(request, view=None):
        wait = throttle.wait()
        response = JsonResponse(
            {"success": False, "error": {"code": "THROTTLED",
             "message": "Too many requests. Please slow down."}},
            status=429,
        )
        if wait is not None:
            response["Retry-After"] = str(int(wait))
        return response
    return None

@require_http_methods(["POST"])
def submit_quiz_attempt(request):
    throttle_response = _check_throttle(request, QuizSubmitThrottle)
    if throttle_response:
        return throttle_response

    if not request.user.is_authenticated or not hasattr(request.user, "student_profile"):
        return JsonResponse({"success": False, "message": "Not authenticated as student."}, status=403)
        
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON."}, status=400)
        
    quiz_id = payload.get("quiz_id")
    if not quiz_id:
        return JsonResponse({"success": False, "message": "quiz_id required."}, status=400)
        
    student = request.user.student_profile
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    answers = payload.get("answers", {})
    # hints_used = payload.get("hints_used", 0)
    # time_taken = payload.get("time_taken", 0)
    
    total_score = 0
    
    with transaction.atomic():
        # Create QuizAttempt
        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            status=QuizAttempt.Status.SUBMITTED,
            submitted_at=timezone.now()
        )
        
        # Calculate scores and save QuestionResponse
        for q_id_str, opt_id in answers.items():
            try:
                question = Question.objects.get(id=int(q_id_str), quizzes=quiz)
                selected_option = Option.objects.get(id=int(opt_id), question=question)
            except (ValueError, Question.DoesNotExist, Option.DoesNotExist):
                continue
            
            is_correct = selected_option.is_correct
            marks_awarded = question.marks if is_correct else -question.negative_marks
            total_score += marks_awarded
            
            # Persist Response
            response = QuestionResponse.objects.create(
                attempt=attempt,
                question=question,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
                answered_at=timezone.now()
            )
            response.selected_options.add(selected_option)
            
        # Update attempt score
        # Cap score to 0 so we don't have negative score overall unless desired
        total_score = max(0, total_score)
        attempt.score = total_score
        attempt.save(update_fields=["score"])
        
        # Calculate percentage (for mastery tracking)
        max_possible_score = sum(q.marks for q in quiz.questions.all())
        percentage = 0
        if max_possible_score > 0:
            percentage = int((total_score / max_possible_score) * 100)
            
        # Update TopicProgress
        tp, created = TopicProgress.objects.get_or_create(
            student=student, 
            topic=quiz.topic
        )
        if percentage > tp.best_score:
            tp.best_score = percentage
        tp.last_activity_at = timezone.now()
        tp.save(update_fields=["best_score", "last_activity_at"])
        
        # Grant XP/Coins based on score
        xp_awarded = int(percentage * 0.5) # Example: 50 XP for 100%
        coins_awarded = int(percentage * 0.1) # Example: 10 Coins for 100%
        
        if xp_awarded > 0 or coins_awarded > 0:
            from apps.gamification.models import XPAccount, XPTransaction, CreditAccount, CreditTransaction
            
            # Award XP
            if xp_awarded > 0:
                xp_acc, _ = XPAccount.objects.get_or_create(student=student)
                XPTransaction.objects.get_or_create(
                    account=xp_acc,
                    reference=f"quiz_attempt_{attempt.id}",
                    defaults={
                        "amount": xp_awarded,
                        "source": XPTransaction.Source.QUIZ,
                        "description": f"Quiz {quiz.title} completed."
                    }
                )
                xp_acc.total_xp += xp_awarded
                xp_acc.save(update_fields=["total_xp"])
                student.xp_points += xp_awarded
                
            # Award Coins
            if coins_awarded > 0:
                credit_acc, _ = CreditAccount.objects.get_or_create(student=student)
                CreditTransaction.objects.get_or_create(
                    account=credit_acc,
                    reference=f"quiz_attempt_{attempt.id}",
                    defaults={
                        "amount": coins_awarded,
                        "transaction_type": CreditTransaction.TransactionType.EARN,
                        "description": f"Quiz {quiz.title} completed."
                    }
                )
                credit_acc.balance += coins_awarded
                credit_acc.save(update_fields=["balance"])
                student.adventure_coins += coins_awarded

            student.save(update_fields=["xp_points", "adventure_coins"])

    return JsonResponse({
        "success": True, 
        "attempt_id": str(attempt.id)
    })
