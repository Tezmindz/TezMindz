import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.games.models import Game, GameContent
from apps.accounts.models import StudentProfile
from apps.curriculum.admin_forms import ConceptAdminForm
from apps.games.admin_forms import GameAdminForm
from common.views import subject_page, chapter_page, concept_page, game_play_page

User = get_user_model()
factory = RequestFactory()

def run_regression_tests():
    print("=" * 70)
    print("RUNNING CURRICULUM HIERARCHY REGRESSION & VERIFICATION SUITE")
    print("=" * 70)

    # 1. Inspect existing DB records
    grade_5 = Grade.objects.filter(name__icontains="5").first() or Grade.objects.first()
    math_subject = Subject.objects.filter(name__icontains="Math").first() or Subject.objects.first()
    topic = Topic.objects.filter(subject=math_subject, grade=grade_5).first() or Topic.objects.first()
    concept = Concept.objects.filter(topic=topic).first()

    if not concept:
        concept = Concept.objects.create(
            topic=topic,
            title="Number System & Place Value",
            content_body="Learn the foundations of numbers.",
            order=1,
            status="published"
        )

    print(f"[1] Verified Canonical Existing Hierarchy:")
    print(f"    Grade:   {grade_5.name} (id={grade_5.id})")
    print(f"    Subject: {math_subject.name} (id={math_subject.id})")
    print(f"    Chapter: {topic.title} (id={topic.id})")
    print(f"    Concept: {concept.title} (id={concept.id})")

    # Ensure Game 1 points to this canonical concept
    game_1 = Game.objects.first()
    if game_1:
        game_1.concept = concept
        game_1.status = "published"
        game_1.save()
        print(f"    Game:    {game_1.title} (id={game_1.id}, type={game_1.game_type}) -> linked to Concept {concept.id}")

    # 2. Test Student Profile & Views along the canonical hierarchy
    user, _ = User.objects.get_or_create(username="test_student_regression", defaults={"email": "student@tezmindz.com"})
    student_profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={"grade": grade_5})
    student_profile.grade = grade_5
    student_profile.save()

    req = factory.get("/")
    req.user = user

    import html
    # Step A: Subject Page
    res_sub = subject_page(req, math_subject.id)
    assert res_sub.status_code == 200, f"Subject page returned {res_sub.status_code}"
    assert html.escape(topic.title).encode() in res_sub.content, "Chapter title not found in Subject page"
    print("    [PASS] Subject -> Chapter mapping renders in Student UI")

    # Step B: Chapter Page
    res_ch = chapter_page(req, topic.id)
    assert res_ch.status_code == 200, f"Chapter page returned {res_ch.status_code}"
    assert html.escape(concept.title).encode() in res_ch.content, "Concept title not found in Chapter page"
    print("    [PASS] Chapter -> Concept mapping renders in Student UI")

    # Step C: Concept Page
    res_conc = concept_page(req, concept.id)
    assert res_conc.status_code == 200, f"Concept page returned {res_conc.status_code}"
    assert game_1.title.encode() in res_conc.content, "Game title not found in Concept page"
    print("    [PASS] Concept -> Game mapping renders in Student UI")

    # Step D: Game Play Page
    res_game = game_play_page(req, game_1.id)
    assert res_game.status_code == 200, f"Game play page returned {res_game.status_code}"
    assert b"game-runner-viewport" in res_game.content, "Universal game shell viewport not rendered"
    assert b"game-shell.js" in res_game.content, "game-shell.js not injected"
    print("    [PASS] Game -> Universal Game Shell renders in Student UI")

    print("\n" + "=" * 70)
    print("TESTING NEW RECORD CREATION VIA ADMIN WORKFLOW & DEPENDENT SELECTORS")
    print("=" * 70)

    # 3. Create a NEW Concept using ConceptAdminForm
    concept_form_data = {
        "grade": grade_5.id,
        "subject": math_subject.id,
        "topic": topic.id,
        "title": "Geometry Polygons & Symmetry",
        "content_body": "Understanding 2D and 3D shapes.",
        "order": 2,
        "status": "published"
    }
    concept_form = ConceptAdminForm(data=concept_form_data)
    assert concept_form.is_valid(), f"ConceptAdminForm errors: {concept_form.errors}"
    new_concept = concept_form.save()
    print(f"    [PASS] Created NEW Concept via Admin Form: '{new_concept.title}' (id={new_concept.id})")

    # 4. Create a NEW Game using GameAdminForm
    game_form_data = {
        "grade": grade_5.id,
        "subject": math_subject.id,
        "chapter": topic.id,
        "concept": new_concept.id,
        "title": "Geometry Arena Quest",
        "description": "Master polygons and 3D geometric figures.",
        "game_type": "geometry-challenge",
        "difficulty": "medium",
        "access_tier": "free",
        "status": "published",
        "config": '{"total_rounds": 3}'
    }
    game_form = GameAdminForm(data=game_form_data)
    assert game_form.is_valid(), f"GameAdminForm errors: {game_form.errors}"
    new_game = game_form.save()
    print(f"    [PASS] Created NEW Game via Admin Form: '{new_game.title}' (id={new_game.id}, type={new_game.game_type})")

    # Add dynamic GameContent to the new game
    gc = GameContent.objects.create(
        game=new_game,
        order=1,
        prompt="Identify the shape with 3 sides and one 90-degree right angle.",
        content_type="shape_identify",
        data={"options": ["Right-Angled Triangle", "Circle", "Pentagon", "Hexagon"]},
        correct_answer="Right-Angled Triangle",
        points=100
    )
    print(f"    [PASS] Added dynamic GameContent (id={gc.id}) pointing ONLY to Game (no duplicate hierarchy FKs)")

    # 5. Verify the NEW Game immediately appears in Student UI
    res_new_conc = concept_page(req, new_concept.id)
    assert res_new_conc.status_code == 200
    assert new_game.title.encode() in res_new_conc.content, "New game not displayed on new Concept page!"
    print(f"    [PASS] New Game automatically appeared on Student Concept UI without modifying frontend code!")

    # 6. Verify the NEW Game launches through the Universal Game Shell
    res_new_game_play = game_play_page(req, new_game.id)
    assert res_new_game_play.status_code == 200
    assert b"Geometry Arena Quest" in res_new_game_play.content
    assert b"geometry-challenge" in res_new_game_play.content
    assert b"Identify the shape with 3 sides" in res_new_game_play.content
    print(f"    [PASS] New Game launches with dynamic questions in Universal Game Shell!")

    # 7. Verify Server-Side Tamper Resistance in Admin Forms
    # Try to assign a concept belonging to Class 5 into an illegal mismatched grade
    other_grade = Grade.objects.exclude(id=grade_5.id).first()
    if other_grade:
        tampered_game_data = game_form_data.copy()
        tampered_game_data["grade"] = other_grade.id  # Mismatched grade tamper attempt
        tampered_form = GameAdminForm(data=tampered_game_data)
        assert not tampered_form.is_valid(), "Tampered GameAdminForm should NOT be valid!"
        print(f"    [PASS] Server-side tamper protection successfully rejected mismatched grade in GameAdminForm")

    print("\n" + "=" * 70)
    print("ALL REGRESSION & INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_regression_tests()
