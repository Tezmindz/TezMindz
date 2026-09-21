import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.db import transaction

from common.throttles import QuizSubmitThrottle
from .models import Quiz, QuizAttempt, QuestionResponse, Question, Option, MockTest, MockTestQuestion, MockTestAttempt, MockTestResponse
from .serializers import MockTestListSerializer, MockTestDetailSerializer
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


@require_http_methods(["GET"])
def mock_test_list_api(request):
    """
    Returns published Mock Tests strictly for the authenticated student's registered Grade.
    Server-side enforcement ensures students NEVER see or access other grades' tests.
    """
    if not request.user.is_authenticated or not hasattr(request.user, "student_profile"):
        return JsonResponse({"success": False, "error": "Not authenticated as student."}, status=403)

    student = request.user.student_profile
    grade = student.grade

    # Strictly filter by authenticated student's grade
    tests = MockTest.objects.filter(grade=grade, status="published").select_related("grade", "subject")

    subject_id = request.GET.get("subject_id")
    if subject_id:
        try:
            tests = tests.filter(subject_id=int(subject_id))
        except (ValueError, TypeError):
            pass

    serializer = MockTestListSerializer(tests, many=True, context={"student": student})
    return JsonResponse({
        "success": True,
        "grade": {"id": grade.id, "name": grade.name},
        "count": len(serializer.data),
        "results": serializer.data
    })


@require_http_methods(["GET"])
def mock_test_detail_api(request, test_id):
    """
    Returns metadata and questions for a Mock Test without revealing answers.
    Server-side validation strictly enforces that the test belongs to student's grade.
    """
    if not request.user.is_authenticated or not hasattr(request.user, "student_profile"):
        return JsonResponse({"success": False, "error": "Not authenticated as student."}, status=403)

    student = request.user.student_profile

    # Query with grade constraint to prevent ID probing
    mock_test = MockTest.objects.filter(id=test_id, grade=student.grade, status="published").first()
    if not mock_test:
        return JsonResponse({"success": False, "error": "Mock test not found or not available for your grade."}, status=404)

    serializer = MockTestDetailSerializer(mock_test)
    return JsonResponse({
        "success": True,
        "mock_test": serializer.data
    })


@require_http_methods(["POST"])
def mock_test_submit_api(request, test_id):
    """
    Processes Mock Test submission, performs server-side scoring, records immutable response
    and attempt objects, and awards XP and Coins.
    """
    throttle_response = _check_throttle(request, QuizSubmitThrottle)
    if throttle_response:
        return throttle_response

    if not request.user.is_authenticated or not hasattr(request.user, "student_profile"):
        return JsonResponse({"success": False, "error": "Not authenticated as student."}, status=403)

    student = request.user.student_profile

    mock_test = MockTest.objects.filter(id=test_id, grade=student.grade, status="published").first()
    if not mock_test:
        return JsonResponse({"success": False, "error": "Mock test not found or not available for your grade."}, status=404)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON."}, status=400)

    answers = payload.get("answers", {}) # dict of { "<question_id>": <option_id_or_list> }
    time_taken_seconds = payload.get("time_taken_seconds", 0)

    # Server-side calculation
    total_score = 0
    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    all_test_questions = mock_test.questions.all().prefetch_related("options")
    computed_total_marks = sum(q.marks for q in all_test_questions)

    with transaction.atomic():
        attempt = MockTestAttempt.objects.create(
            student=student,
            mock_test=mock_test,
            status=MockTestAttempt.Status.SUBMITTED,
            submitted_at=timezone.now(),
            total_marks=computed_total_marks,
        )

        for q in all_test_questions:
            user_selection = answers.get(str(q.id))
            if user_selection is None:
                user_selection = answers.get(q.id)

            if user_selection is None:
                unanswered_count += 1
                response = MockTestResponse.objects.create(
                    attempt=attempt,
                    question=q,
                    is_correct=False,
                    marks_awarded=0,
                    answered_at=timezone.now()
                )
                continue

            # Selected options
            selected_option_ids = []
            if isinstance(user_selection, list):
                selected_option_ids = [int(x) for x in user_selection if str(x).isdigit()]
            elif str(user_selection).isdigit():
                selected_option_ids = [int(user_selection)]

            selected_opts = list(q.options.filter(id__in=selected_option_ids))

            # Determine correctness
            correct_opts = set(q.options.filter(is_correct=True).values_list("id", flat=True))
            student_opts = set(selected_opts_obj.id for selected_opts_obj in selected_opts)

            is_correct = (correct_opts == student_opts) and len(correct_opts) > 0

            if is_correct:
                marks_awarded = q.marks
                correct_count += 1
            else:
                marks_awarded = -q.negative_marks
                wrong_count += 1

            total_score += marks_awarded

            resp = MockTestResponse.objects.create(
                attempt=attempt,
                question=q,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
                answered_at=timezone.now()
            )
            if selected_opts:
                resp.selected_options.set(selected_opts)

        total_score = max(0, total_score)
        percentage = int((total_score / computed_total_marks) * 100) if computed_total_marks > 0 else 0

        attempt.score = total_score
        attempt.percentage = percentage
        attempt.save(update_fields=["score", "percentage"])

        # Rewards (XP and Coins)
        xp_awarded = int(percentage * 0.8) # e.g. 80 XP for 100%
        coins_awarded = int(percentage * 0.25) # e.g. 25 Coins for 100%

        if xp_awarded > 0 or coins_awarded > 0:
            from apps.gamification.models import XPAccount, XPTransaction, CreditAccount, CreditTransaction

            if xp_awarded > 0:
                xp_acc, _ = XPAccount.objects.get_or_create(student=student)
                XPTransaction.objects.get_or_create(
                    account=xp_acc,
                    reference=f"mock_test_attempt_{attempt.id}",
                    defaults={
                        "amount": xp_awarded,
                        "source": XPTransaction.Source.QUIZ,
                        "description": f"Mock Test '{mock_test.title}' completed with {percentage}%."
                    }
                )
                xp_acc.total_xp += xp_awarded
                xp_acc.save(update_fields=["total_xp"])
                student.xp_points += xp_awarded

            if coins_awarded > 0:
                credit_acc, _ = CreditAccount.objects.get_or_create(student=student)
                CreditTransaction.objects.get_or_create(
                    account=credit_acc,
                    reference=f"mock_test_attempt_{attempt.id}",
                    defaults={
                        "amount": coins_awarded,
                        "transaction_type": CreditTransaction.TransactionType.EARN,
                        "description": f"Mock Test '{mock_test.title}' reward."
                    }
                )
                credit_acc.balance += coins_awarded
                credit_acc.save(update_fields=["balance"])
                student.adventure_coins += coins_awarded

            student.save(update_fields=["xp_points", "adventure_coins"])

    return JsonResponse({
        "success": True,
        "attempt_id": str(attempt.public_id),
        "attempt_db_id": attempt.id,
        "score": total_score,
        "total_marks": computed_total_marks,
        "percentage": percentage,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "unanswered_count": unanswered_count,
        "xp_awarded": xp_awarded,
        "coins_awarded": coins_awarded
    })

