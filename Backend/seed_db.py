import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import StudentProfile, AccountStatus
from apps.curriculum.models import Grade, Subject, Topic
from apps.curriculum.models import Concept
from apps.games.models import Game, GameContent, AccessTier
from apps.assessments.models import Quiz, Question, Option, QuizQuestion
from apps.gamification.models import XPAccount, CreditAccount, XPLevelThreshold

User = get_user_model()

def seed():
    print("=== Seeding TezMindz database... ===")

    # 1. Level thresholds
    levels_data = [
        (1, 0),
        (2, 100),
        (3, 250),
        (4, 500),
        (5, 1000),
        (6, 2000),
    ]
    for lvl, xp in levels_data:
        XPLevelThreshold.objects.get_or_create(level=lvl, defaults={"xp_required": xp})

    # 2. Grades
    grades = {}
    for i in range(1, 6):
        g, _ = Grade.objects.get_or_create(order=i, defaults={"name": f"Class {i}"})
        grades[i] = g
    g5 = grades[5]

    # 3. Subjects
    subjects_data = [
        ("Mathematics", "mathematics", 1),
        ("Science", "science", 2),
        ("English", "english", 3),
    ]
    subjects = {}
    for name, slug, order in subjects_data:
        s, _ = Subject.objects.get_or_create(name=name, defaults={"slug": slug, "order": order})
        subjects[slug] = s

    math = subjects["mathematics"]
    science = subjects["science"]

    # 4. Chapters / Topics
    topics_data = [
        (math, g5, "Number & Operations", 1),
        (math, g5, "Geometry & Shapes", 2),
        (math, g5, "Fractions & Decimals", 3),
        (science, g5, "Living Organisms & Habitat", 1),
    ]
    topics = {}
    for sub, grd, title, order in topics_data:
        t, _ = Topic.objects.get_or_create(
            title=title, subject=sub,
            defaults={"grade": grd, "order": order, "status": "published"}
        )
        if t.grade != grd:
            t.grade = grd
            t.status = "published"
            t.save()
        topics[title] = t

    top_numbers = topics["Number & Operations"]
    top_geometry = topics["Geometry & Shapes"]
    top_fractions = topics["Fractions & Decimals"]

    # 5. Concepts
    c_numbers, _ = Concept.objects.get_or_create(
        topic=top_numbers,
        title="Number System & Place Value",
        defaults={
            "order": 1,
            "status": "published",
            "content_body": "Master the Indian and International place value systems, large numbers, and rounding."
        }
    )

    c_geometry, _ = Concept.objects.get_or_create(
        topic=top_geometry,
        title="Polygons & 3D Geometry",
        defaults={
            "order": 1,
            "status": "published",
            "content_body": "Explore polygons, vertex counts, edges, and 3D architectural shapes."
        }
    )

    c_fractions, _ = Concept.objects.get_or_create(
        topic=top_fractions,
        title="Fraction Pizza & Equivalent Parts",
        defaults={
            "order": 1,
            "status": "published",
            "content_body": "Visualizing fractions through interactive pizza slice division and equivalence."
        }
    )

    # 6. Games & Game Content
    games_data = [
        {
            "title": "Dream House Builder 3D",
            "concept": c_numbers,
            "game_type": "house-builder",
            "difficulty": "medium",
            "description": "Construct 3D architectural marvels by solving math problems!",
            "config": {"total_stages": 5, "starting_funds": 1000},
            "contents": [
                {"order": 1, "prompt": "Solve 45 x 6 to buy foundation cement", "points": 15},
                {"order": 2, "prompt": "Place value of 7 in 74,520 to install structural pillars", "points": 20},
            ]
        },
        {
            "title": "Number Train Adventure",
            "concept": c_numbers,
            "game_type": "number-train",
            "difficulty": "easy",
            "description": "Ride the express number train across India and master place values!",
            "config": {"speed": "normal", "wagons": 6},
            "contents": [
                {"order": 1, "prompt": "Load passenger carriages in ascending place value", "points": 10},
            ]
        },
        {
            "title": "Pizza Fraction Challenge",
            "concept": c_fractions,
            "game_type": "fraction-pizza",
            "difficulty": "easy",
            "description": "Bake delicious pizzas while learning fractions and equal divisions.",
            "config": {"slices": [4, 6, 8]},
            "contents": [
                {"order": 1, "prompt": "Serve 3/4 of a mushroom pizza to customer 1", "points": 10},
            ]
        },
        {
            "title": "Geometry Arena Quest",
            "concept": c_geometry,
            "game_type": "geometry-challenge",
            "difficulty": "medium",
            "description": "Duel in the geometry arena by identifying angles, symmetry, and polyhedra.",
            "config": {"rounds": 3},
            "contents": [
                {"order": 1, "prompt": "Identify the regular hexagon with perimeter 36 cm", "points": 15},
            ]
        }
    ]

    for g_info in games_data:
        gm = Game.objects.filter(title=g_info["title"]).first()
        if not gm:
            gm = Game.objects.create(
                title=g_info["title"],
                concept=g_info["concept"],
                game_type=g_info["game_type"],
                difficulty=g_info["difficulty"],
                description=g_info["description"],
                status="published",
                access_tier=AccessTier.FREE,
                config=g_info["config"],
            )
        else:
            gm.concept = g_info["concept"]
            gm.status = "published"
            gm.save()

        for c_item in g_info["contents"]:
            GameContent.objects.get_or_create(
                game=gm,
                order=c_item["order"],
                defaults={
                    "prompt": c_item["prompt"],
                    "points": c_item["points"]
                }
            )

    # 7. Quizzes
    quiz_math, _ = Quiz.objects.get_or_create(
        title="Number Systems Mastery Quiz",
        topic=top_numbers,
        defaults={"status": "published", "duration_seconds": 600}
    )

    q1, _ = Question.objects.get_or_create(
        prompt="What is the place value of 9 in 492,305?",
        defaults={"concept": c_numbers, "topic": top_numbers, "status": "published", "marks": 10}
    )
    QuizQuestion.objects.get_or_create(quiz=quiz_math, question=q1, defaults={"order": 1})
    Option.objects.get_or_create(question=q1, text="90,000", defaults={"is_correct": True, "order": 1})
    Option.objects.get_or_create(question=q1, text="9,000", defaults={"is_correct": False, "order": 2})
    Option.objects.get_or_create(question=q1, text="900", defaults={"is_correct": False, "order": 3})
    Option.objects.get_or_create(question=q1, text="90", defaults={"is_correct": False, "order": 4})

    # 8. Demo Superuser (Admin)
    admin_user, created_admin = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@tezmindz.in",
            "role": User.Role.ADMIN,
            "is_staff": True,
            "is_superuser": True
        }
    )
    admin_user.set_password("admin123")
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()

    # 9. Demo Student
    student_user, created_student = User.objects.get_or_create(
        username="student",
        defaults={
            "email": "student@tezmindz.in",
            "role": User.Role.STUDENT,
        }
    )
    student_user.set_password("student123")
    student_user.save()

    student_profile, _ = StudentProfile.objects.get_or_create(
        user=student_user,
        defaults={
            "display_name": "Aarav Sharma",
            "grade": g5,
            "avatar_key": StudentProfile.Avatar.COMET,
            "account_status": AccountStatus.ACTIVE,
            "xp_points": 350,
            "adventure_coins": 120,
            "daily_streak": 4,
        }
    )
    # 10. Subscription Plans
    from apps.subscriptions.models import Plan
    plans_data = [
        {
            "code": "online-g14",
            "name": "Online only (Grade 1–4)",
            "price": "299.00",
            "billing_period": Plan.BillingPeriod.MONTHLY,
            "features": {
                "tier": "online",
                "tier_name": "Online only",
                "grade_band": "Grade 1–4",
                "badge": "Junior Wing",
                "bullet_points": [
                    "100% Full Online Platform Access",
                    "Full Access to All 3D Gamified Worlds (Dream House, Fraction Pizza, Number Train)",
                    "Interactive Concept Notes & Visual Notes for Core Subjects",
                    "Adaptive Olympiad Quizzes with Instant Explanations & Hints",
                    "AI Doubt Assistant & Live Telemetry Streak Tracking",
                    "Weekly Parent Progress Reports & Skill Mastery Heatmaps"
                ]
            }
        },
        {
            "code": "online-g58",
            "name": "Online only (Grade 5–8)",
            "price": "399.00",
            "billing_period": Plan.BillingPeriod.MONTHLY,
            "features": {
                "tier": "online",
                "tier_name": "Online only",
                "grade_band": "Grade 5–8",
                "badge": "Senior Wing",
                "bullet_points": [
                    "100% Full Online Platform Access",
                    "Full Access to All 3D Gamified Worlds (Dream House, Fraction Pizza, Number Train)",
                    "Interactive Concept Notes & Visual Notes for Core Subjects",
                    "Adaptive Olympiad Quizzes with Instant Explanations & Hints",
                    "AI Doubt Assistant & Live Telemetry Streak Tracking",
                    "Weekly Parent Progress Reports & Skill Mastery Heatmaps"
                ]
            }
        },
        {
            "code": "hybrid-g14",
            "name": "Physical Centre + Online (Grade 1–4)",
            "price": "999.00",
            "billing_period": Plan.BillingPeriod.MONTHLY,
            "features": {
                "tier": "hybrid",
                "tier_name": "Physical Centre + Online",
                "grade_band": "Grade 1–4",
                "badge": "Most Popular • Hybrid",
                "bullet_points": [
                    "Everything in Online Only",
                    "Weekly Physical Classroom Sessions at TezMindz Learning Centres",
                    "Dedicated 1-on-1 Certified Olympiad Faculty Mentorship",
                    "Physical Mock Olympiad Exam Series with Simulated OMR Grading",
                    "Hands-on Science & Math Activity Kits for Centre Labs",
                    "Printed Revision Workbooks, Summary Mindmaps & Formula Sheets",
                    "In-person Parent-Teacher Review & Olympiad Strategy Consultations"
                ]
            }
        },
        {
            "code": "hybrid-g58",
            "name": "Physical Centre + Online (Grade 5–8)",
            "price": "1299.00",
            "billing_period": Plan.BillingPeriod.MONTHLY,
            "features": {
                "tier": "hybrid",
                "tier_name": "Physical Centre + Online",
                "grade_band": "Grade 5–8",
                "badge": "Most Popular • Hybrid",
                "bullet_points": [
                    "Everything in Online Only",
                    "Weekly Physical Classroom Sessions at TezMindz Learning Centres",
                    "Dedicated 1-on-1 Certified Olympiad Faculty Mentorship",
                    "Physical Mock Olympiad Exam Series with Simulated OMR Grading",
                    "Hands-on Science & Math Activity Kits for Centre Labs",
                    "Printed Revision Workbooks, Summary Mindmaps & Formula Sheets",
                    "In-person Parent-Teacher Review & Olympiad Strategy Consultations"
                ]
            }
        },
    ]

    for pdata in plans_data:
        p, created = Plan.objects.get_or_create(
            code=pdata["code"],
            defaults={
                "name": pdata["name"],
                "price": pdata["price"],
                "billing_period": pdata["billing_period"],
                "features": pdata["features"],
                "is_active": True
            }
        )
        if not created:
            p.name = pdata["name"]
            p.price = pdata["price"]
            p.billing_period = pdata["billing_period"]
            p.features = pdata["features"]
            p.is_active = True
            p.save()

    print(" Database seeded successfully with curriculum, users, and subscription plans!")
    print("--------------------------------------------------")
    print(" Superuser:  username='admin'   password='admin123'")
    print(" Student:    username='student' password='student123'")
    print("--------------------------------------------------")

if __name__ == "__main__":
    seed()
