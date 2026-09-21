import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from common.throttles import AuthEndpointThrottle


def template_page(template_name):
    def view(request, *args, **kwargs):
        return render(request, template_name)

    return view

def achievements_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/achievements/")
    from apps.gamification.models import Badge, StudentBadge
    
    all_badges = Badge.objects.filter(is_active=True).order_by('name')
    earned_badges_ids = set()
    
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        earned_badges_ids = set(StudentBadge.objects.filter(
            student=request.user.student_profile
        ).values_list('badge_id', flat=True))
        
    achievements = []
    for b in all_badges:
        xp_reward = b.criteria.get('xp_reward', 50) if isinstance(b.criteria, dict) else 50
        coin_reward = b.criteria.get('coin_reward', 10) if isinstance(b.criteria, dict) else 10
        
        achievements.append({
            'name': b.name,
            'description': b.description,
            'icon': b.icon_key or '🏆',
            'xp_reward': xp_reward,
            'coin_reward': coin_reward,
            'is_earned': b.id in earned_badges_ids,
        })
        
    context = {
        'achievements': achievements,
        'earned_count': len(earned_badges_ids),
        'total_count': len(all_badges),
    }
    return render(request, "achievements.html", context)

def learn_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/learn/")
    from apps.curriculum.models import Subject
    from apps.progress.models import TopicProgress
    grade = None
    profile = None
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        grade = profile.grade
        
    subjects = Subject.objects.all().order_by('order', 'name')
    class_subjects = []
    
    total_curriculum_topics = 0
    total_mastered_topics = 0
    current_learning_subject = None
    
    for s in subjects:
        topics = s.topics.filter(grade=grade, status='published').order_by('order', 'id') if grade else s.topics.filter(status='published').order_by('order', 'id')
        total_topics = topics.count()
        done_topics = 0
        tp_dict = {}
        if profile and total_topics > 0:
            tp_list = TopicProgress.objects.filter(student=profile, topic__in=topics)
            tp_dict = {tp.topic_id: tp for tp in tp_list}
            done_topics = sum(1 for tp in tp_list if tp.best_score >= 60)
            total_curriculum_topics += total_topics
            total_mastered_topics += done_topics
            
        progress_pct = int((done_topics / total_topics) * 100) if total_topics > 0 else 0
        
        enriched_chapters = []
        next_topic_to_continue = None
        is_prev_mastered = True
        for idx, ch in enumerate(topics):
            tp = tp_dict.get(ch.id)
            score = tp.best_score if tp else 0
            attempts = tp.attempts if tp else 0
            stars = compute_star_rating(score)
            meta = get_world_metadata(ch, idx)

            is_unlocked = (idx == 0) or is_prev_mastered or (hasattr(request, 'user') and request.user.is_staff)

            if score >= 80:
                ch_status = "completed"
                ch_status_label = "Mastered"
                badge_text = "🏆 MASTERED"
                ch_progress = 100
            elif attempts > 0 or score > 0:
                ch_status = "in_progress"
                ch_status_label = "In Progress"
                badge_text = "⚡ IN PROGRESS"
                ch_progress = max(25, min(80, int((score / 60) * 100)))
                if not next_topic_to_continue:
                    next_topic_to_continue = ch
            elif is_unlocked:
                ch_status = "unlocked"
                ch_status_label = "Ready"
                badge_text = "🔓 READY"
                ch_progress = 0
                if not next_topic_to_continue and done_topics == 0:
                    next_topic_to_continue = ch
            else:
                ch_status = "locked"
                ch_status_label = "Locked"
                badge_text = "🔒 LOCKED"
                ch_progress = 0

            is_prev_mastered = (score >= 50)
            
            concept_count = ch.concepts.filter(status='published').count() if hasattr(ch, 'concepts') else 0
            if concept_count == 0:
                concept_count = 3
            completed_modules = int((ch_progress / 100) * concept_count)
            games_count = ch.concepts.filter(status='published', games__status='published').distinct().count() if hasattr(ch, 'concepts') else 0
            
            enriched_chapters.append({
                "id": ch.id,
                "order": ch.order or (idx + 1),
                "name": ch.name,
                "title": ch.title,
                "difficulty": ch.difficulty,
                "status": ch_status,
                "status_label": ch_status_label,
                "badge_text": badge_text,
                "is_unlocked": is_unlocked,
                "progress_pct": ch_progress,
                "total_modules": concept_count,
                "completed_modules": completed_modules,
                "stars": stars,
                "games_count": games_count,
                "meta": meta,
            })
            
        if not next_topic_to_continue and topics.exists():
            for ch in topics:
                tp = tp_dict.get(ch.id)
                if not tp or tp.best_score < 60:
                    next_topic_to_continue = ch
                    break
            if not next_topic_to_continue:
                next_topic_to_continue = topics.first()
                
        if progress_pct > 0 and not current_learning_subject:
            current_learning_subject = {
                "name": s.name,
                "slug": getattr(s, 'slug', ''),
                "progress_pct": progress_pct,
                "topic": next_topic_to_continue
            }

        topic_titles = [t.title for t in topics[:3]]
        subtopics_str = " • ".join(topic_titles) if topic_titles else "Curriculum In Progress"

        s_name_lower = s.name.lower()
        s_slug = getattr(s, 'slug', '') or ''
        if 'math' in s_name_lower or 'math' in s_slug:
            icon_type = 'math'
            theme_color = '#2563EB'
            theme_bg = '#EFF6FF'
            theme_pill = '#DBEAFE'
            icon_emoji = '🔢'
            olympiad_code = 'IMO'
        elif 'sci' in s_name_lower or 'sci' in s_slug or 'bio' in s_name_lower:
            icon_type = 'science'
            theme_color = '#059669'
            theme_bg = '#ECFDF5'
            theme_pill = '#D1FAE5'
            icon_emoji = '🧪'
            olympiad_code = 'NSO'
        elif 'eng' in s_name_lower or 'eng' in s_slug:
            icon_type = 'english'
            theme_color = '#DB2777'
            theme_bg = '#FDF2F8'
            theme_pill = '#FCE7F3'
            icon_emoji = '📚'
            olympiad_code = 'IEO'
        else:
            icon_type = 'general'
            theme_color = '#7C3AED'
            theme_bg = '#FAF5FF'
            theme_pill = '#EDE9FE'
            icon_emoji = '🌟'
            olympiad_code = 'OLYMPIAD'
        
        total_modules_count = sum(c['total_modules'] for c in enriched_chapters)
        completed_modules_count = sum(c['completed_modules'] for c in enriched_chapters)

        class_subjects.append({
            "id": s.id,
            "name": s.name,
            "slug": s_slug,
            "subject": s,
            "icon_type": icon_type,
            "icon_emoji": icon_emoji,
            "theme_color": theme_color,
            "theme_bg": theme_bg,
            "theme_pill": theme_pill,
            "olympiad_code": olympiad_code,
            "subtopics_str": subtopics_str,
            "total_concepts": total_topics,
            "done_concepts": done_topics,
            "total_modules": total_modules_count or (total_topics * 3),
            "done_modules": completed_modules_count,
            "remaining_modules": max(0, (total_modules_count or (total_topics * 3)) - completed_modules_count),
            "progress_pct": progress_pct,
            "current_topic": next_topic_to_continue,
            "has_started": (done_topics > 0 or progress_pct > 0 or any(c['status'] == 'in_progress' for c in enriched_chapters)),
            "chapters": enriched_chapters
        })
        
    today_xp = 0
    daily_goal_xp = 200
    if profile:
        today_xp = profile.xp_points % daily_goal_xp if profile.xp_points > 0 else 0
        if today_xp == 0 and profile.xp_points > 0:
            today_xp = daily_goal_xp
    xp_to_goal = max(0, daily_goal_xp - today_xp)
    xp_progress_pct = int((today_xp / daily_goal_xp) * 100)

    overall_progress_pct = int((total_mastered_topics / total_curriculum_topics) * 100) if total_curriculum_topics > 0 else 0

    total_stars_count = sum(sum(ch.get("stars", 0) for ch in s.get("chapters", [])) for s in class_subjects)
    credits_balance = 0
    if profile:
        try:
            from apps.rewards.models import CreditAccount
            acct = CreditAccount.objects.filter(student=profile).first()
            if acct:
                credits_balance = acct.balance
        except Exception:
            credits_balance = 0

    student_name = ""
    if profile and profile.display_name:
        student_name = profile.display_name
    elif hasattr(request, 'user') and request.user.is_authenticated:
        student_name = request.user.get_full_name() or getattr(request.user, 'first_name', '') or request.user.username
    if not student_name:
        student_name = "Champion"

    if total_mastered_topics > 0:
        mascot_quote = f"Incredible work, {student_name}! You've mastered {total_mastered_topics} Adventure Worlds! Ready to unlock the next realm?"
    elif xp_progress_pct > 0:
        mascot_quote = f"Awesome streak, {student_name}! Conquer your next adventure quest today and level up your skills!"
    else:
        mascot_quote = f"Welcome to the Learning Worlds, {student_name}! I'm Tezzy, your cosmic adventure guide. Choose a realm below to start your quest!"

    context = {
        "student_name": student_name,
        "student_class": grade,
        "profile": profile,
        "class_subjects": class_subjects,
        "current_learning": current_learning_subject or ({"name": class_subjects[0]["name"], "slug": class_subjects[0]["slug"], "progress_pct": class_subjects[0]["progress_pct"], "topic": class_subjects[0]["current_topic"]} if class_subjects else None),
        "overall_progress_pct": overall_progress_pct,
        "total_mastered_topics": total_mastered_topics,
        "total_curriculum_topics": total_curriculum_topics,
        "total_stars": total_stars_count,
        "credits_balance": credits_balance,
        "today_xp": today_xp,
        "daily_goal_xp": daily_goal_xp,
        "xp_to_goal": xp_to_goal,
        "xp_progress_pct": xp_progress_pct,
        "streak_days": getattr(profile, 'daily_streak', 0) if profile else 0,
        "mascot_quote": mascot_quote,
    }
    return render(request, "learn.html", context)


def dashboard_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/dashboard/")

    if request.user.is_staff or request.user.is_superuser:
        # Strict role separation: administrators must access administrative console, not student dashboard
        return redirect("/admin/")

    if not hasattr(request.user, 'student_profile'):
        return redirect("/")

    from apps.curriculum.models import Subject
    from apps.accounts.models import StudentProfile
    from apps.progress.models import TopicProgress
    from apps.gamification.models import DailyChallenge
    from django.utils import timezone

    profile = request.user.student_profile
    grade = profile.grade

    # Authoritative subjects query ordered by order and name
    subjects = Subject.objects.all().order_by('order', 'name')

    class_subjects = []
    for s in subjects:
        # Grade-scoped chapters strictly evaluated per subject
        topics = s.topics.filter(grade=grade, status='published').order_by('order', 'id')
        total_topics = topics.count()

        # Count completed topics (mastery >= 60) for this student
        tp_list = TopicProgress.objects.filter(student=profile, topic__in=topics)
        done_topics = sum(1 for tp in tp_list if tp.best_score >= 60)
        progress_pct = int((done_topics / total_topics) * 100) if total_topics > 0 else 0

        # Subtopics preview dynamically derived from actual topics of this subject in this grade
        topic_titles = [t.title for t in topics[:2]]
        if topic_titles:
            subtopics_str = " • ".join(topic_titles)
        else:
            subtopics_str = "Curriculum In Progress"

        # Dynamic theme & Olympiad badge mapping based on subject identity
        s_slug = getattr(s, 'slug', '') or ''
        s_name_lower = s.name.lower()
        s_slug_lower = s_slug.lower()

        if 'math' in s_name_lower or 'math' in s_slug_lower:
            theme_class = 'w-math'
            olympiad_badge = 'IMO • Math'
            xp_bounty = '⚡ +120 XP'
            accent_color = '#2563EB'
        elif 'sci' in s_name_lower or 'sci' in s_slug_lower or 'bio' in s_name_lower:
            theme_class = 'w-science'
            olympiad_badge = 'NSO • Science'
            xp_bounty = '⚡ +150 XP'
            accent_color = '#059669'
        elif 'eng' in s_name_lower or 'eng' in s_slug_lower:
            theme_class = 'w-english'
            olympiad_badge = 'IEO • English'
            xp_bounty = '⚡ +100 XP'
            accent_color = '#DB2777'
        elif 'social' in s_name_lower or 'social' in s_slug_lower or 'history' in s_name_lower or 'geo' in s_name_lower:
            theme_class = 'w-social'
            olympiad_badge = f'ISSO • {s.name}'
            xp_bounty = '⚡ +110 XP'
            accent_color = '#D97706'
        else:
            theme_class = 'w-purple'
            olympiad_badge = f'OLYMPIAD • {s.name}'
            xp_bounty = '⚡ +100 XP'
            accent_color = '#7C3AED'

        class_subjects.append({
            "id": s.id,
            "name": s.name,
            "slug": s_slug,
            "subtopics": subtopics_str,
            "olympiad_badge": olympiad_badge,
            "xp_bounty": xp_bounty,
            "theme_class": theme_class,
            "accent_color": accent_color,
            "total_concepts": total_topics,
            "done_concepts": done_topics,
            "progress_pct": progress_pct,
        })

    classmates = StudentProfile.objects.filter(grade=grade).exclude(id=profile.id).order_by('-xp_points')[:4]

    # Daily challenge
    today = timezone.now().date()
    daily_challenge_obj = DailyChallenge.objects.filter(is_published=True, active_date__lte=today).order_by('-active_date').first()

    if daily_challenge_obj:
        target_url = "#"
        if daily_challenge_obj.topic:
            target_url = f"/subject/{daily_challenge_obj.topic.subject_id}/"
        elif daily_challenge_obj.game and daily_challenge_obj.game.concept:
            target_url = f"/concept/{daily_challenge_obj.game.concept.id}/"
        elif daily_challenge_obj.quiz and daily_challenge_obj.quiz.concept:
            target_url = f"/quiz/{daily_challenge_obj.quiz.id}/"

        today_challenge = {
            "title": daily_challenge_obj.title,
            "description": daily_challenge_obj.description,
            "xp_reward": daily_challenge_obj.xp_reward,
            "coin_reward": daily_challenge_obj.coin_reward,
            "url": target_url
        }
    else:
        today_challenge = None

    # Mock Test Arena data for student's registered grade
    from apps.assessments.models import MockTest, MockTestAttempt
    grade_mock_tests = MockTest.objects.filter(grade=grade, status="published").select_related("grade", "subject")
    mock_tests_count = grade_mock_tests.count()

    mock_test_featured = None
    if mock_tests_count > 0:
        attempted_test_ids = set(MockTestAttempt.objects.filter(student=profile, mock_test__in=grade_mock_tests, status="submitted").values_list("mock_test_id", flat=True))
        for mt in grade_mock_tests:
            if mt.id not in attempted_test_ids:
                mock_test_featured = mt
                break
        if not mock_test_featured:
            mock_test_featured = grade_mock_tests.first()

        best_att = MockTestAttempt.objects.filter(student=profile, mock_test=mock_test_featured, status="submitted").order_by("-percentage").first()
        mock_test_featured.student_best_percentage = best_att.percentage if best_att else None
        mock_test_featured.student_best_score = best_att.score if best_att else None
        mock_test_featured.student_attempts_count = MockTestAttempt.objects.filter(student=profile, mock_test=mock_test_featured, status="submitted").count()

    context = {
        "class_subjects": class_subjects,
        "profile": profile,
        "classmates": classmates,
        "today_challenge": today_challenge,
        "mock_test_featured": mock_test_featured,
        "mock_tests_count": mock_tests_count,
    }
    return render(request, "dashboard.html", context)


def mock_tests_arena_page(request):
    """
    Dedicated student-facing Mock Test Arena list page.
    Strictly filters Mock Tests by the student's registered Grade.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/login/?next=/mock-tests/")
    if not hasattr(request.user, 'student_profile'):
        return redirect("/")

    from apps.assessments.models import MockTest, MockTestAttempt
    from apps.curriculum.models import Subject
    profile = request.user.student_profile
    grade = profile.grade

    # Strictly filter by student's grade
    tests = MockTest.objects.filter(grade=grade, status="published").select_related("grade", "subject").order_by("order", "id")

    subject_slug = request.GET.get("subject")
    if subject_slug and subject_slug != "all":
        tests = tests.filter(subject__slug=subject_slug)

    enriched_tests = []
    total_completed = 0
    total_percentage_sum = 0
    best_overall_pct = 0

    student_attempts = MockTestAttempt.objects.filter(student=profile, mock_test__in=tests, status="submitted")
    attempts_by_test = {}
    for att in student_attempts:
        attempts_by_test.setdefault(att.mock_test_id, []).append(att)

    for t in tests:
        atts = attempts_by_test.get(t.id, [])
        best_pct = max((a.percentage for a in atts), default=None)
        if best_pct is not None:
            total_completed += 1
            total_percentage_sum += best_pct
            if best_pct > best_overall_pct:
                best_overall_pct = best_pct

        enriched_tests.append({
            "test": t,
            "best_percentage": best_pct,
            "attempts_count": len(atts),
            "is_completed": best_pct is not None,
            "is_passed": (best_pct >= t.passing_percentage) if best_pct is not None else False,
        })

    avg_pct = int(total_percentage_sum / total_completed) if total_completed > 0 else 0
    subjects = Subject.objects.filter(topics__grade=grade).distinct()

    context = {
        "profile": profile,
        "grade": grade,
        "tests": enriched_tests,
        "tests_count": len(enriched_tests),
        "total_completed": total_completed,
        "avg_percentage": avg_pct,
        "best_overall_pct": best_overall_pct,
        "subjects": subjects,
        "active_subject": subject_slug or "all",
    }
    return render(request, "mock_tests/arena.html", context)


def mock_test_take_page(request, test_id):
    """
    Interactive Mock Test taking interface.
    Validates grade server-side (returns 404 if test does not belong to student's grade).
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/login/?next=/mock-tests/{test_id}/")
    if not hasattr(request.user, 'student_profile'):
        return redirect("/")

    from django.shortcuts import get_object_or_404
    from apps.assessments.models import MockTest
    profile = request.user.student_profile

    # Server-side validation: student can ONLY take tests for their registered grade
    mock_test = get_object_or_404(MockTest, id=test_id, grade=profile.grade, status="published")

    test_questions = mock_test.test_questions.select_related("question").prefetch_related("question__options").order_by("order", "id")

    questions_list = []
    for tq in test_questions:
        q = tq.question
        opts = list(q.options.all().order_by("order", "id"))
        questions_list.append({
            "id": q.id,
            "test_order": tq.order,
            "prompt": q.prompt,
            "difficulty": q.difficulty,
            "marks": q.marks,
            "negative_marks": q.negative_marks,
            "allow_multiple": q.allow_multiple_answers,
            "options": [{"id": o.id, "text": o.text, "order": o.order} for o in opts],
        })

    import json
    context = {
        "profile": profile,
        "grade": profile.grade,
        "mock_test": mock_test,
        "questions": questions_list,
        "questions_json": json.dumps(questions_list),
        "total_questions": len(questions_list),
        "duration_seconds": mock_test.duration_seconds,
        "duration_minutes": mock_test.duration_minutes,
    }
    return render(request, "mock_tests/take.html", context)


def mock_test_result_page(request, attempt_id):
    """
    Mock Test results and answer review screen.
    Validates attempt ownership so students cannot inspect other students' attempts.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/login/")
    if not hasattr(request.user, 'student_profile'):
        return redirect("/")

    from django.shortcuts import get_object_or_404
    from apps.assessments.models import MockTestAttempt
    profile = request.user.student_profile

    # Authoritative ownership check
    attempt = get_object_or_404(
        MockTestAttempt.objects.select_related("mock_test", "mock_test__grade", "mock_test__subject", "student"),
        public_id=attempt_id,
        student=profile
    )

    responses = attempt.responses.select_related("question").prefetch_related("selected_options", "question__options")

    correct_count = sum(1 for r in responses if r.is_correct is True)
    wrong_count = sum(1 for r in responses if r.is_correct is False and r.selected_options.exists())
    unanswered_count = sum(1 for r in responses if not r.selected_options.exists())

    time_taken_secs = 0
    if attempt.submitted_at and attempt.started_at:
        time_taken_secs = int((attempt.submitted_at - attempt.started_at).total_seconds())

    mins = time_taken_secs // 60
    secs = time_taken_secs % 60
    time_taken_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

    from apps.gamification.models import XPTransaction, CreditTransaction
    xp_txn = XPTransaction.objects.filter(reference=f"mock_test_attempt_{attempt.id}").first()
    coin_txn = CreditTransaction.objects.filter(reference=f"mock_test_attempt_{attempt.id}").first()

    context = {
        "profile": profile,
        "grade": profile.grade,
        "attempt": attempt,
        "mock_test": attempt.mock_test,
        "responses": responses,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "unanswered_count": unanswered_count,
        "time_taken_str": time_taken_str,
        "xp_earned": xp_txn.amount if xp_txn else int(attempt.percentage * 0.8),
        "coins_earned": coin_txn.amount if coin_txn else int(attempt.percentage * 0.25),
        "passed": attempt.percentage >= attempt.mock_test.passing_percentage,
    }
    return render(request, "mock_tests/result.html", context)


def get_world_metadata(topic, index=0):
    """
    Returns student-facing 'World' metadata for a Topic/Chapter.
    """
    title_lower = topic.title.lower()
    order_num = topic.order or (index + 1)
    
    if "number" in title_lower:
        world_name = "Number Valley"
        theme_badge = "Valley of Numbers"
        theme_color = "#10B981"
        theme_gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
        bg_image = "/static/media/adventure/world_number_valley.jpg"
        icon_emoji = "🌳"
        tagline = "Master place values, large numbers, and arithmetic puzzles."
    elif "fraction" in title_lower or "decimal" in title_lower:
        world_name = "Fraction Kingdom"
        theme_badge = "Kingdom of Parts"
        theme_color = "#F59E0B"
        theme_gradient = "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)"
        bg_image = "/static/media/adventure/world_fraction_kingdom.jpg"
        icon_emoji = "🍕"
        tagline = "Bake pizza fractions, balance decimals, and conquer ratios."
    elif "geometry" in title_lower or "shape" in title_lower:
        world_name = "Geometry Island"
        theme_badge = "Floating Crystal Island"
        theme_color = "#6366F1"
        theme_gradient = "linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)"
        bg_image = "/static/media/adventure/world_geometry_island.jpg"
        icon_emoji = "💎"
        tagline = "Explore 3D polyhedra, angles, symmetry, and architectural shapes."
    elif "organism" in title_lower or "habitat" in title_lower or "science" in title_lower:
        world_name = "Living Habitat Jungle"
        theme_badge = "Ecosystem Canopy"
        theme_color = "#059669"
        theme_gradient = "linear-gradient(135deg, #059669 0%, #047857 100%)"
        bg_image = "/static/media/adventure/world_number_valley.jpg"
        icon_emoji = "🌿"
        tagline = "Discover habitats, adaptations, and natural wonders."
    else:
        world_name = f"World {order_num} — {topic.title}"
        theme_badge = "Adventure Zone"
        theme_color = "#7C3AED"
        theme_gradient = "linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)"
        bg_image = "/static/media/adventure/world_number_valley.jpg"
        icon_emoji = "✨"
        tagline = topic.description or f"Complete exciting missions in {topic.title}."

    return {
        "world_number": order_num,
        "world_name": world_name,
        "original_title": topic.title,
        "theme_badge": theme_badge,
        "theme_color": theme_color,
        "theme_gradient": theme_gradient,
        "bg_image": bg_image,
        "icon_emoji": icon_emoji,
        "tagline": tagline,
    }


def compute_star_rating(score):
    if score >= 90:
        return 5
    if score >= 75:
        return 4
    if score >= 60:
        return 3
    if score >= 40:
        return 2
    if score > 0:
        return 1
    return 0


def world_detail_page(request, world_id):
    from django.shortcuts import redirect
    return redirect("common:subject", subject_id=world_id)


def subject_page(request, subject_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/subject/{subject_id}/")
    from django.shortcuts import get_object_or_404
    from apps.curriculum.models import Subject
    from apps.progress.models import TopicProgress
    from apps.games.models import Game
    from apps.assessments.models import Quiz
    subject = get_object_or_404(Subject, id=subject_id)

    student_class = None
    profile = None
    if hasattr(request, "user") and request.user.is_authenticated and hasattr(request.user, "student_profile"):
        profile = request.user.student_profile
        grade = profile.grade
        topics = list(subject.topics.filter(grade=grade, status="published").prefetch_related("concepts__games").order_by("order", "id"))
        student_class = grade
    else:
        topics = list(subject.topics.filter(status="published").prefetch_related("concepts__games").order_by("order", "id"))

    tp_map = {}
    if profile and topics:
        tp_map = {tp.topic_id: tp for tp in TopicProgress.objects.filter(student=profile, topic__in=topics)}

    completed_worlds_count = 0
    total_stars_earned = 0
    enriched_worlds = []
    today_mission = None

    for idx, ch in enumerate(topics):
        tp = tp_map.get(ch.id)
        score = tp.best_score if tp else 0
        ch.progress_pct = score

        # Concepts and games count
        concepts = list(ch.concepts.filter(status="published"))
        ch.total_concepts = len(concepts)
        has_quiz = ch.quizzes.filter(status="published").exists()
        ch.adventures_count = len(concepts) + (1 if has_quiz else 0)

        # Star rating
        stars = compute_star_rating(score)
        total_stars_earned += stars
        ch.stars = stars
        ch.stars_display = [{"earned": i <= stars} for i in range(1, 6)]

        # Adventures completed count
        if score >= 60:
            ch.adventures_done = ch.adventures_count
        elif score > 0:
            ch.adventures_done = max(1, int((score / 100) * ch.adventures_count))
        else:
            ch.adventures_done = 0

        # Unlocked / Locked progression rule
        if idx == 0:
            unlocked = True
        else:
            prev_topic = topics[idx - 1]
            prev_score = prev_topic.progress_pct
            unlocked = (prev_score >= 50) or (hasattr(request, "user") and getattr(request.user, "is_staff", False))

        if not unlocked:
            ch.status_key = "locked"
            ch.status_label = "Locked"
        elif score >= 80:
            ch.status_key = "completed"
            ch.status_label = "Mastered"
            completed_worlds_count += 1
        elif score > 0 or (tp and tp.attempts > 0):
            ch.status_key = "in_progress"
            ch.status_label = "In Progress"
        else:
            ch.status_key = "unlocked"
            ch.status_label = "Ready to Play"

        ch.is_unlocked = unlocked
        ch.world_meta = get_world_metadata(ch, idx)

        # Games available in this world
        ch_games = list(Game.objects.filter(concept__topic=ch, status="published").distinct()[:3])
        ch.available_games = ch_games

        enriched_worlds.append(ch)

        # Determine Today's Mission (first unlocked & unfinished world)
        if today_mission is None and unlocked and score < 80:
            next_concept = concepts[0] if concepts else None
            today_mission = {
                "world": ch,
                "world_name": ch.world_meta["world_name"],
                "title": next_concept.title if next_concept else f"Explore {ch.title}",
                "url": f"/concept/{next_concept.id}/" if next_concept else f"/chapter/{ch.id}/",
                "type": "Adventure Mission",
                "bg_image": ch.world_meta["bg_image"],
                "theme_color": ch.world_meta["theme_color"],
            }

    # Fallback today's mission if all completed or none found
    if today_mission is None and enriched_worlds:
        first_w = enriched_worlds[0]
        today_mission = {
            "world": first_w,
            "world_name": first_w.world_meta["world_name"],
            "title": f"Review & Practice {first_w.title}",
            "url": f"/chapter/{first_w.id}/",
            "type": "Championship Review",
            "bg_image": first_w.world_meta["bg_image"],
            "theme_color": first_w.world_meta["theme_color"],
        }

    # Dynamic adventure title
    s_lower = subject.name.lower()
    if "math" in s_lower:
        adventure_title = "Math Adventure World"
        adventure_tagline = "Explore kingdoms, solve 3D challenges, and earn cosmic rewards!"
    elif "sci" in s_lower or "bio" in s_lower:
        adventure_title = "Science Discovery World"
        adventure_tagline = "Uncover mysteries of nature, habitats, and experimental simulations!"
    else:
        adventure_title = f"{subject.name} Adventure World"
        adventure_tagline = f"Embark on an epic learning quest through {subject.name}!"

    context = {
        "subject": subject,
        "chapters": enriched_worlds,
        "student_class": student_class,
        "adventure_title": adventure_title,
        "adventure_tagline": adventure_tagline,
        "total_worlds": len(enriched_worlds),
        "completed_worlds": completed_worlds_count,
        "total_stars_earned": total_stars_earned,
        "max_stars_possible": len(enriched_worlds) * 5,
        "today_mission": today_mission,
        "profile": profile,
        "xp_points": profile.xp_points if profile else 0,
        "adventure_coins": profile.adventure_coins if profile else 0,
        "daily_streak": profile.daily_streak if profile else 0,
    }
    return render(request, "subject.html", context)


def chapter_page(request, chapter_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/chapter/{chapter_id}/")
    from django.shortcuts import get_object_or_404
    from apps.curriculum.models import Topic
    from apps.progress.models import TopicProgress
    from apps.games.models import Game
    chapter = get_object_or_404(Topic, id=chapter_id)

    concepts = list(chapter.concepts.filter(status="published").prefetch_related("games").order_by("order", "id"))

    student_class = None
    tp = None
    if hasattr(request, "user") and request.user.is_authenticated and hasattr(request.user, "student_profile"):
        student = request.user.student_profile
        student_class = student.grade
        tp = TopicProgress.objects.filter(student=student, topic=chapter).first()

    score = tp.best_score if tp else 0
    is_mastered = score >= 60
    has_activity = (tp.last_activity_at is not None) if tp else False
    has_game = (tp.attempts > 0) if tp else False

    # Chapter Quiz as "Boss Challenge"
    quiz = chapter.quizzes.filter(status="published").first()

    # Enrich each concept as an Adventure Milestone Node
    enriched_nodes = []
    for i, conc in enumerate(concepts):
        game = conc.games.filter(status="published").first()
        
        # Progression state for node
        if is_mastered:
            node_status = "mastered"
        elif i == 0 or has_activity:
            node_status = "active"
        else:
            node_status = "available"

        conc.progress = {
            "is_mastered": is_mastered,
            "learn_completed": has_activity or is_mastered or (i == 0),
            "game_completed": has_game or is_mastered,
            "quiz_completed": is_mastered,
            "node_status": node_status,
        }
        conc.first_game = game
        enriched_nodes.append(conc)

    # Next Chapter / World for transition
    next_chapter = Topic.objects.filter(
        subject=chapter.subject,
        grade=chapter.grade,
        order__gt=chapter.order,
        status="published"
    ).order_by("order").first()

    world_meta = get_world_metadata(chapter)
    stars = compute_star_rating(score)

    context = {
        "chapter": chapter,
        "concepts": enriched_nodes,
        "student_class": student_class,
        "world_meta": world_meta,
        "boss_quiz": quiz,
        "progress_score": score,
        "is_mastered": is_mastered,
        "stars": stars,
        "stars_display": [{"earned": i <= stars} for i in range(1, 6)],
        "next_chapter": next_chapter,
    }
    return render(request, "chapter.html", context)

def concept_page(request, concept_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/concept/{concept_id}/")
    from django.shortcuts import get_object_or_404
    from apps.curriculum.models import Concept
    from apps.assessments.models import Quiz
    from apps.progress.models import TopicProgress
    concept = get_object_or_404(Concept, id=concept_id)
    
    first_game = concept.games.filter(status='published').first()
    
    # Query quiz matching this concept, or fall back to chapter quiz
    first_quiz = Quiz.published.filter(questions__concept=concept).first()
    if not first_quiz and hasattr(concept.topic, 'quizzes'):
        first_quiz = concept.topic.quizzes.filter(status='published').first()

    # Resolve TopicProgress based on available model fields
    tp = None
    student_class = None
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        tp = TopicProgress.objects.filter(student=request.user.student_profile, topic=concept.topic).first()
        student_class = request.user.student_profile.grade

    topic_progress = {
        "learn_completed": tp.last_activity_at is not None if tp else False,
        "game_unlocked": tp.last_activity_at is not None if tp else False,
        "game_completed": tp.attempts > 0 if tp else False,
        "quiz_unlocked": tp.attempts > 0 if tp else False,
        "quiz_completed": tp.best_score >= 60 if tp else False,
        "mastery_percentage": tp.best_score if tp else 0,
    }

    return render(request, "concept.html", {
        "concept": concept, 
        "chapter": concept.topic,
        "first_game": first_game,
        "first_quiz": first_quiz,
        "topic_progress": topic_progress,
        "student_class": student_class
    })

def quiz_page(request, quiz_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/quiz/{quiz_id}/")
    from django.shortcuts import get_object_or_404
    from apps.assessments.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related("options")
    return render(request, "quiz.html", {"quiz": quiz, "questions": questions})

def quiz_result_page(request, attempt_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/quiz/result/{attempt_id}/")
    from django.shortcuts import get_object_or_404
    from apps.assessments.models import QuizAttempt
    from apps.curriculum.models import Concept
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    responses = attempt.responses.select_related("question").prefetch_related("selected_options")
    
    # Calculate metrics
    total_marks = sum(q.marks for q in attempt.quiz.questions.all())
    percentage = int((attempt.score / total_marks) * 100) if total_marks > 0 else 0
    passed = percentage >= 60
    
    attempt.total_marks = total_marks
    attempt.percentage = percentage
    attempt.passed = passed
    
    # Fetch real XP earned from Gamification Ledger
    from apps.gamification.models import XPTransaction
    txn = XPTransaction.objects.filter(reference=f"quiz_attempt_{attempt.id}").first()
    attempt.xp_earned = txn.amount if txn else 0
    
    if attempt.submitted_at and attempt.started_at:
        attempt.time_taken = int((attempt.submitted_at - attempt.started_at).total_seconds())
    else:
        attempt.time_taken = 0
        
    next_concept = None
    if passed and hasattr(attempt.quiz, 'topic') and attempt.quiz.topic:
        current_concept = Concept.objects.filter(topic=attempt.quiz.topic).first()
        if current_concept:
            next_concept = Concept.objects.filter(topic=current_concept.topic, order__gt=current_concept.order).order_by('order').first()
            
    return render(request, "quiz_result.html", {
        "quiz": attempt.quiz, 
        "attempt": attempt, 
        "responses": responses,
        "next_concept": next_concept
    })

def game_difficulty_page(request, game_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/game/{game_id}/difficulty/")
    from django.shortcuts import get_object_or_404
    from apps.games.models import Game
    game = get_object_or_404(Game, id=game_id)
    return render(request, "difficulty.html", {"game": game})

def game_play_page(request, game_id):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect(f"/?auth=login&next=/game/{game_id}/play/")
    import json
    from django.shortcuts import get_object_or_404
    from apps.games.models import Game
    game = get_object_or_404(Game.published, id=game_id)
    
    questions_data = []
    for gc in game.contents.all().order_by("order"):
        questions_data.append({
            "id": gc.id,
            "order": gc.order,
            "prompt": gc.prompt,
            "content_type": gc.content_type,
            "data": gc.data,
            "points": gc.points,
            "hints": gc.hints,
            "correct_answer": gc.correct_answer,
        })

    student_data = {}
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        student_data = {
            "name": request.user.get_full_name() or request.user.username,
            "grade": str(profile.grade) if profile.grade else "",
            "coins": getattr(profile, 'adventure_coins', 0),
            "xp": getattr(profile, 'xp_points', 0),
        }

    game_context = {
        "game_id": game.id,
        "id": game.id,
        "title": game.title,
        "game_type": game.game_type,
        "difficulty": game.difficulty,
        "access_tier": game.access_tier,
        "config": game.config or {},
        "questions": questions_data,
        "csrfToken": request.META.get("CSRF_COOKIE", ""),
        "student": student_data,
    }

    if game.concept:
        game_context["concept"] = {
            "id": game.concept.id,
            "title": game.concept.title,
        }
        if game.concept.topic:
            game_context["topic"] = {
                "id": game.concept.topic.id,
                "title": game.concept.topic.title,
                "subject": game.concept.topic.subject.name if game.concept.topic.subject else "",
            }

    context = {
        "game": game,
        "game_context_json": json.dumps(game_context),
        "csrf_token": request.META.get("CSRF_COOKIE", ""),
    }

    return render(request, "games/game_shell.html", context)

def games_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/games/")
    from apps.games.models import Game, GameSession
    from django.db.models import Q
    student_class = None
    profile = None
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        student_class = profile.grade
        games_qs = Game.published.filter(
            Q(concept__topic__grade=student_class) | Q(concept__isnull=True)
        ).distinct().order_by('id')
    else:
        games_qs = Game.published.all().order_by('id')
        
    enriched_games = []
    recent_session = None
    if profile:
        recent_session = GameSession.objects.filter(student=profile).order_by('-started_at').first()
        
    for g in games_qs:
        subject_name = "General"
        subject_slug = "general"
        if g.concept and g.concept.topic and g.concept.topic.subject:
            subject_name = g.concept.topic.subject.name
            subject_slug = g.concept.topic.subject.slug or g.concept.topic.subject.name.lower()
        
        g_title_lower = g.title.lower()
        if 'pizza' in g_title_lower or 'fraction' in g_title_lower or 'math' in subject_slug:
            emoji = '🍕'
            subject_category = 'Mathematics'
            category_slug = 'math'
            theme_color = '#2563EB'
            theme_bg = '#EFF6FF'
            theme_pill = '#DBEAFE'
            xp_reward = 150
            coin_reward = 15
            is_flagship = True
        elif 'bio' in g_title_lower or 'reactor' in g_title_lower or 'science' in subject_slug:
            emoji = '🧪'
            subject_category = 'Science'
            category_slug = 'science'
            theme_color = '#059669'
            theme_bg = '#ECFDF5'
            theme_pill = '#D1FAE5'
            xp_reward = 160
            coin_reward = 16
            is_flagship = False
        elif 'sentence' in g_title_lower or 'token' in g_title_lower or 'english' in subject_slug:
            emoji = '📝'
            subject_category = 'English'
            category_slug = 'english'
            theme_color = '#DB2777'
            theme_bg = '#FDF2F8'
            theme_pill = '#FCE7F3'
            xp_reward = 140
            coin_reward = 14
            is_flagship = False
        elif 'house' in g_title_lower or 'builder' in g_title_lower:
            emoji = '🏠'
            subject_category = '3D Worlds'
            category_slug = 'math'
            theme_color = '#7C3AED'
            theme_bg = '#FAF5FF'
            theme_pill = '#EDE9FE'
            xp_reward = 200
            coin_reward = 25
            is_flagship = True
        else:
            emoji = '🎮'
            subject_category = subject_name
            category_slug = 'general'
            theme_color = '#6366F1'
            theme_bg = '#EEF2FF'
            theme_pill = '#E0E7FF'
            xp_reward = 100
            coin_reward = 10
            is_flagship = False

        diff = g.difficulty.capitalize() if g.difficulty else "Medium"
        if diff == "Easy":
            diff_color = "#059669"
            diff_bg = "#ECFDF5"
        elif diff == "Hard":
            diff_color = "#DC2626"
            diff_bg = "#FEF2F2"
        else:
            diff_color = "#D97706"
            diff_bg = "#FFFBEB"

        enriched_games.append({
            "id": g.id,
            "title": g.title,
            "description": g.description or f"Master key {subject_category} concepts through engaging 3D gameplay and interactive levels.",
            "game_type": g.game_type,
            "difficulty": diff,
            "difficulty_color": diff_color,
            "difficulty_bg": diff_bg,
            "subject_category": subject_category,
            "category_slug": category_slug,
            "emoji": emoji,
            "theme_color": theme_color,
            "theme_bg": theme_bg,
            "theme_pill": theme_pill,
            "xp_reward": xp_reward,
            "coin_reward": coin_reward,
            "is_flagship": is_flagship,
            "concept_name": g.concept.title if g.concept else "",
            "topic_name": g.concept.topic.title if (g.concept and g.concept.topic) else "",
        })

    featured_game = None
    if recent_session and recent_session.game:
        # find matching dict
        for gm in enriched_games:
            if gm['id'] == recent_session.game.id:
                featured_game = gm
                break
    if not featured_game and enriched_games:
        featured_game = next((gm for gm in enriched_games if gm['is_flagship']), enriched_games[0])

    context = {
        "games": enriched_games,
        "profile": profile,
        "student_class": student_class,
        "featured_game": featured_game,
        "total_games_count": len(enriched_games),
        "total_xp": getattr(profile, 'xp_points', 0) if profile else 0,
        "total_coins": getattr(profile, 'adventure_coins', 0) if profile else 0,
        "streak_days": getattr(profile, 'daily_streak', 0) if profile else 0,
    }
    return render(request, "games.html", context)

def progress_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/progress/")
    from apps.curriculum.models import Subject
    from apps.progress.models import TopicProgress
    student_class = None
    profile = None
    subject_progress = []
    recent_logs = []
    
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        student_class = profile.grade
        subjects = Subject.objects.all().order_by('order', 'name')
        
        for s in subjects:
            topics = s.topics.filter(grade=student_class, status='published')
            total_topics = topics.count()
            tps = TopicProgress.objects.filter(student=profile, topic__in=topics)
            mastered = sum(1 for tp in tps if tp.best_score >= 60)
            pct = int((mastered / total_topics) * 100) if total_topics > 0 else 0
            subject_progress.append({
                "subject": s,
                "cs": {"subject": s},
                "pct": pct,
                "mastered": mastered,
                "total": total_topics
            })
            
        recent_logs = TopicProgress.objects.filter(
            student=profile, last_activity_at__isnull=False
        ).select_related('topic', 'topic__subject').order_by('-last_activity_at')[:10]
        
    return render(request, "progress.html", {
        "student_class": student_class,
        "profile": profile,
        "subject_progress": subject_progress,
        "recent_logs": recent_logs
    })

def leaderboard_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/leaderboard/")
    from apps.accounts.models import StudentProfile
    student_class = None
    profile = None
    leaderboard = []
    
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        student_class = profile.grade
        students = StudentProfile.objects.filter(grade=student_class).select_related('user').order_by('-xp_points', 'id')[:20]
    else:
        students = StudentProfile.objects.select_related('user', 'grade').order_by('-xp_points', 'id')[:20]
        
    for idx, s in enumerate(students):
        leaderboard.append({
            "rank": idx + 1,
            "student": s,
            "name": s.display_name or s.user.first_name or s.user.username,
            "xp": s.xp_points,
            "is_current_user": (profile and s.id == profile.id),
        })
        
    return render(request, "leaderboard.html", {
        "student_class": student_class,
        "profile": profile,
        "leaderboard": leaderboard
    })

def rewards_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/rewards/")
    from apps.gamification.models import Badge, StudentBadge, XPTransaction, CreditTransaction
    student_class = None
    profile = None
    earned_badge_ids = set()
    xp_history = []
    coin_history = []
    
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        student_class = profile.grade
        earned_badge_ids = set(StudentBadge.objects.filter(student=profile).values_list('badge_id', flat=True))
        if hasattr(profile, 'xp_account'):
            xp_history = XPTransaction.objects.filter(account=profile.xp_account).order_by('-created_at')[:8]
        if hasattr(profile, 'credit_account'):
            coin_history = CreditTransaction.objects.filter(account=profile.credit_account).order_by('-created_at')[:8]
            
    all_badges = Badge.objects.filter(is_active=True).order_by('name')
    badges = []
    for b in all_badges:
        badges.append({
            "name": b.name,
            "description": b.description,
            "icon": b.icon_key or "🏆",
            "is_earned": b.id in earned_badge_ids,
        })
        
    return render(request, "rewards.html", {
        "student_class": student_class,
        "profile": profile,
        "badges": badges,
        "xp_history": xp_history,
        "coin_history": coin_history
    })

def profile_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/profile/")
    student_class = None
    profile = None
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        student_class = profile.grade
    return render(request, "profile.html", {"profile": profile, "student_class": student_class})

@require_http_methods(["GET", "POST"])
def login_page(request):
    if request.method == "GET":
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
                return redirect("/admin/")
            return redirect("/dashboard/")
        query_string = request.META.get("QUERY_STRING", "")
        if query_string:
            return redirect(f"/?auth=login&{query_string}")
        return redirect("/?auth=login")

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    identifier = (
        payload.get("identifier")
        or payload.get("email")
        or payload.get("phone")
        or payload.get("phone_number")
        or payload.get("username")
        or ""
    ).strip()
    password = payload.get("password") or ""

    if not identifier or not password:
        return JsonResponse({"success": False, "message": "Email or phone number and password are required."}, status=400)

    from apps.accounts.utils import normalize_phone_number
    from apps.accounts.models import StudentProfile

    user = None
    if "@" in identifier:
        user = authenticate(request, username=identifier, password=password)
    else:
        normalized_phone = normalize_phone_number(identifier)
        if normalized_phone:
            profile = StudentProfile.objects.filter(phone_number=normalized_phone).select_related("user").first()
            if profile and profile.user:
                user = authenticate(request, username=profile.user.username, password=password)
        elif identifier in ("student", "demo_student"):
            user = authenticate(request, username=identifier, password=password)

    if user is None:
        return JsonResponse({"success": False, "message": "Invalid email/phone or password. Please try again."}, status=400)

    if user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'admin':
        return JsonResponse({
            "success": False,
            "message": "Admin accounts cannot login here. Please use the Admin Portal."
        }, status=403)

    login(request, user)
    
    # Generate JWT tokens for API usage
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    
    return JsonResponse({
        "success": True, 
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "redirect_url": "/dashboard/"
    })

@require_http_methods(["GET", "POST"])
def register_page(request):
    if request.method == "GET":
        if hasattr(request, 'user') and request.user.is_authenticated:
            return redirect("/dashboard/")
        query_string = request.META.get("QUERY_STRING", "")
        if query_string:
            return redirect(f"/?auth=register&{query_string}")
        return redirect("/?auth=register")

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    from apps.accounts.utils import normalize_phone_number, generate_internal_username
    from apps.accounts.models import StudentProfile
    from apps.curriculum.models import Grade

    name = (payload.get("name") or payload.get("fullName") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    raw_phone = (payload.get("phone") or payload.get("phone_number") or "").strip()
    password = payload.get("password") or ""

    if not name:
        return JsonResponse({"success": False, "message": "Please enter your full name."}, status=400)

    if not email or "@" not in email:
        return JsonResponse({"success": False, "message": "Please enter a valid email address."}, status=400)

    normalized_phone = normalize_phone_number(raw_phone)
    if not normalized_phone:
        return JsonResponse({"success": False, "message": "Please enter a valid 10-digit mobile number."}, status=400)

    if not password or len(password) < 6:
        return JsonResponse({"success": False, "message": "Password must be at least 6 characters."}, status=400)

    user_model = get_user_model()
    if user_model.objects.filter(email__iexact=email).exists():
        return JsonResponse({"success": False, "message": "That email is already registered."}, status=400)

    if StudentProfile.objects.filter(phone_number=normalized_phone).exists():
        return JsonResponse({"success": False, "message": "That phone number is already registered."}, status=400)

    # Auto-generate unique internal username (students never manually choose one)
    username = (payload.get("username") or "").strip() or generate_internal_username(name)
    if user_model.objects.filter(username=username).exists():
        username = generate_internal_username(name)

    user = user_model.objects.create_user(username=username, email=email, password=password)
    user.first_name = name
    user.save(update_fields=["first_name"])

    # Resolve Grade
    class_level = payload.get("classLevel")
    grade_obj = None
    if class_level:
        try:
            level_int = int(class_level)
            grade_obj = Grade.objects.filter(order=level_int).first() or Grade.objects.filter(name=str(level_int)).first()
        except (ValueError, TypeError):
            pass
    if not grade_obj:
        grade_obj = Grade.objects.first()

    if grade_obj:
        StudentProfile.objects.create(
            user=user,
            display_name=name,
            phone_number=normalized_phone,
            grade=grade_obj,
        )

    login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
    
    # Generate JWT tokens for API usage
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    
    return JsonResponse({
        "success": True, 
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "redirect_url": "/dashboard/"
    })


@require_http_methods(["GET", "POST"])
def class_page(request):
    if request.method == "POST":
        return JsonResponse({"success": True})
    return render(request, "class.html")


def logout_page(request):
    logout(request)
    return redirect("/")

@csrf_protect
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthEndpointThrottle])
def tezadmin_login_api_view(request):
    if request.method == "GET":
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect("/admin/")
        return render(request, "admin/login.html", {"next": request.GET.get("next", "/admin/")})

    identifier = (request.data.get("identifier") or request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    
    user = authenticate(request, username=identifier, password=password)
    if user is None and "@" in identifier:
        account = get_user_model().objects.filter(email__iexact=identifier).first()
        if account:
            user = authenticate(request, username=account.username, password=password)
            
    if user is None:
        return Response({"success": False, "message": "Invalid credentials."}, status=401)
        
    if not (user.is_staff or user.is_superuser):
        return Response({"success": False, "message": "Unauthorized. Staff access required."}, status=403)
        
    login(request, user)
    
    redirect_url = request.data.get("next") or "/admin/"
    return Response({"success": True, "redirect_url": redirect_url})


def tezadmin_hub_page(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return redirect("/tezadmin/login/")
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("/dashboard/")
    return redirect("/admin/")


@require_http_methods(["POST"])
def learn_complete_api_view(request):
    """
    Mark concept learning completed by updating TopicProgress.last_activity_at.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required."}, status=401)
        
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({"success": False, "message": "Student profile required."}, status=403)
        
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON."}, status=400)
        
    concept_id = payload.get("concept_id")
    if not concept_id:
        return JsonResponse({"success": False, "message": "concept_id is required."}, status=400)
        
    from apps.curriculum.models import Concept
    from apps.progress.models import TopicProgress
    from django.utils import timezone
    
    concept = Concept.objects.filter(id=concept_id).select_related('topic').first()
    if not concept:
        return JsonResponse({"success": False, "message": "Concept not found."}, status=404)
        
    student = request.user.student_profile
    tp, created = TopicProgress.objects.get_or_create(student=student, topic=concept.topic)
    tp.last_activity_at = timezone.now()
    tp.save()
    
    return JsonResponse({"success": True, "message": "Lesson completed successfully."})


def subscription_page(request):
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return redirect("/?auth=login&next=/subscription/")

    profile = getattr(request.user, "student_profile", None)
    student_class = profile.grade if profile else None

    from apps.subscriptions.models import Plan, Subscription, Payment
    from django.utils import timezone

    today = timezone.now().date()
    active_subscription = None
    subscription_history = []
    payments_history = []
    all_plans = list(Plan.objects.filter(is_active=True).order_by("price"))

    if profile:
        active_subscription = (
            Subscription.objects.filter(
                student=profile,
                status=Subscription.Status.ACTIVE,
                end_date__gte=today,
            )
            .select_related("plan")
            .order_by("-end_date")
            .first()
        )
        subscription_history = list(
            Subscription.objects.filter(student=profile)
            .select_related("plan")
            .order_by("-start_date")
        )
        payments_history = list(
            Payment.objects.filter(student=profile)
            .select_related("subscription", "subscription__plan")
            .order_by("-created_at")
        )

    return render(
        request,
        "subscription.html",
        {
            "profile": profile,
            "student_class": student_class,
            "active_subscription": active_subscription,
            "all_plans": all_plans,
            "subscription_history": subscription_history,
            "payments_history": payments_history,
            "today": today,
        },
    )


def subscription_checkout_page(request):
    plan_id = request.GET.get("plan") or request.GET.get("plan_id")
    plan_code = request.GET.get("code") or request.GET.get("plan_code")

    if not hasattr(request, "user") or not request.user.is_authenticated:
        target_param = f"plan={plan_id}" if plan_id else (f"code={plan_code}" if plan_code else "")
        redirect_url = f"/register/?{target_param}" if target_param else "/register/"
        return redirect(redirect_url)

    profile = getattr(request.user, "student_profile", None)
    student_class = profile.grade if profile else None

    from apps.subscriptions.models import Plan, Subscription
    from django.utils import timezone

    today = timezone.now().date()
    selected_plan = None
    if plan_id:
        if plan_id.isdigit():
            selected_plan = Plan.objects.filter(id=int(plan_id), is_active=True).first()
        else:
            selected_plan = Plan.objects.filter(code=plan_id, is_active=True).first()
    elif plan_code:
        selected_plan = Plan.objects.filter(code=plan_code, is_active=True).first()

    if not selected_plan:
        selected_plan = Plan.objects.filter(is_active=True).order_by("price").first()

    active_subscription = None
    if profile:
        active_subscription = (
            Subscription.objects.filter(
                student=profile,
                status=Subscription.Status.ACTIVE,
                end_date__gte=today,
            )
            .select_related("plan")
            .first()
        )

    all_plans = list(Plan.objects.filter(is_active=True).order_by("price"))

    return render(
        request,
        "subscription_checkout.html",
        {
            "profile": profile,
            "student_class": student_class,
            "selected_plan": selected_plan,
            "active_subscription": active_subscription,
            "all_plans": all_plans,
        },
    )


