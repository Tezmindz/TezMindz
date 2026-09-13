import os
import json
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.curriculum.models import Subject, Topic, Concept, Grade
from apps.games.models import Game
from apps.assessments.models import Quiz, Question, Option, QuizQuestion
from apps.accounts.models import StudentProfile

User = get_user_model()
grade5 = Grade.objects.filter(name='5').first() or Grade.objects.first()

# Create test student
user, _ = User.objects.get_or_create(username='pipeline_student', defaults={'email': 'pipe@test.com', 'role': 'STUDENT'})
user.set_password('Pass1234!')
user.save()
profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'grade': grade5, 'xp_points': 100, 'adventure_coins': 50})

try:
    # 1. Admin creates Subject
    sub, _ = Subject.objects.get_or_create(name='Integration Test Subject', defaults={'slug': 'integration-test-subject', 'order': 99})

    # 2. Admin creates Chapter (Topic)
    top, _ = Topic.objects.get_or_create(title='Integration Test Chapter', subject=sub, grade=grade5, defaults={'order': 1, 'status': 'published'})

    # 3. Admin creates Concept
    con, _ = Concept.objects.get_or_create(title='Integration Test Concept', topic=top, defaults={'order': 1, 'status': 'published', 'content_body': 'Concept test description'})

    # 4. Admin creates Game
    gm, _ = Game.objects.get_or_create(title='Integration Test Game', concept=con, defaults={'status': 'published', 'game_type': 'math_challenge'})

    # 5. Admin creates Quiz
    qz, _ = Quiz.objects.get_or_create(title='Integration Test Quiz', topic=top, defaults={'status': 'published', 'duration_seconds': 300})
    q1, _ = Question.objects.get_or_create(prompt='What is 2 + 2?', defaults={'concept': con, 'topic': top, 'status': 'published', 'marks': 10})
    QuizQuestion.objects.get_or_create(quiz=qz, question=q1, defaults={'order': 1})
    o1, _ = Option.objects.get_or_create(question=q1, text='4', defaults={'is_correct': True, 'order': 1})
    o2, _ = Option.objects.get_or_create(question=q1, text='5', defaults={'is_correct': False, 'order': 2})

    print('=== E2E Pipeline Data Created ===')

    client = Client()
    client.force_login(user)

    # A. Student Dashboard
    resp_dash = client.get('/dashboard/')
    assert 'Integration Test Subject' in resp_dash.content.decode('utf-8'), 'Subject not in Dashboard'
    print('A. Subject on Dashboard: PASS')

    # B. Student Subject Page
    resp_sub = client.get(f'/subject/{sub.id}/')
    assert 'Integration Test Chapter' in resp_sub.content.decode('utf-8'), 'Chapter not on Subject Page'
    print('B. Chapter on Subject Page: PASS')

    # C. Student Chapter Page
    resp_ch = client.get(f'/chapter/{top.id}/')
    assert 'Integration Test Concept' in resp_ch.content.decode('utf-8'), 'Concept not on Chapter Page'
    print('C. Concept on Chapter Page: PASS')

    # D. Student Concept Page
    resp_con = client.get(f'/concept/{con.id}/')
    html_con = resp_con.content.decode('utf-8')
    assert 'Integration Test Game' in html_con, 'Game not on Concept Page'
    assert f'/game/{gm.id}/play/' in html_con, 'Game play link not on Concept Page'
    assert f'/quiz/{qz.id}/' in html_con, 'Quiz link not on Concept Page'
    print('D. Game and Quiz on Concept Page: PASS')

    # E. Game Play Page
    resp_gm = client.get(f'/game/{gm.id}/play/')
    assert resp_gm.status_code == 200, f'Game play returned {resp_gm.status_code}'
    print('E. Game Play Page: PASS')

    # F. Game Direct Submission
    init_xp = profile.xp_points
    init_coins = profile.adventure_coins
    resp_submit_gm = client.post('/api/game/submit/', data=json.dumps({
        'game_id': gm.id,
        'score': 100,
        'accuracy': 100,
        'time_taken_seconds': 45
    }), content_type='application/json')
    assert resp_submit_gm.status_code == 200, f'Game submit failed: {resp_submit_gm.content}'
    profile.refresh_from_db()
    print(f'F. Game Submit: XP {init_xp} -> {profile.xp_points}, Coins {init_coins} -> {profile.adventure_coins}: PASS')
    assert profile.xp_points > init_xp, 'XP not incremented by game'

    # G. Quiz Page
    resp_qz = client.get(f'/quiz/{qz.id}/')
    assert resp_qz.status_code == 200, f'Quiz returned {resp_qz.status_code}'
    html_qz = resp_qz.content.decode('utf-8')
    assert 'What is 2 + 2?' in html_qz, 'Quiz question not in Quiz page'
    print('G. Quiz Page Questions: PASS')

    # H. Quiz Submission
    prev_xp = profile.xp_points
    resp_submit_qz = client.post('/api/quiz/submit/', data=json.dumps({
        'quiz_id': qz.id,
        'answers': {str(q1.id): o1.id},
        'time_taken': 30
    }), content_type='application/json')
    assert resp_submit_qz.status_code == 200, f'Quiz submit failed: {resp_submit_qz.content}'
    profile.refresh_from_db()
    res_data = resp_submit_qz.json()
    print(f"H. Quiz Submit: XP {prev_xp} -> {profile.xp_points}, Passed: {res_data.get('passed')}: PASS")

finally:
    # Clean up test records
    Quiz.objects.filter(title='Integration Test Quiz').delete()
    Game.objects.filter(title='Integration Test Game').delete()
    Concept.objects.filter(title='Integration Test Concept').delete()
    Topic.objects.filter(title='Integration Test Chapter').delete()
    Subject.objects.filter(name='Integration Test Subject').delete()
    User.objects.filter(username='pipeline_student').delete()
    print('=== Cleaned up test records successfully! ===')
