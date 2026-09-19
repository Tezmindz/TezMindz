import logging
from django.db import transaction
from django.utils import timezone
from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.assessments.models import Question, Option, Hint, Quiz, QuizQuestion
from apps.games.models import Game, GameContent
from apps.bulk_import.models import BulkImportJob

logger = logging.getLogger("tezmindz.importer")


class ImportEngine:
    """
    Executes the validated rows into existing database models inside an atomic transaction.
    """

    @classmethod
    def execute_import(cls, job: BulkImportJob, rows_to_import: list = None) -> bool:
        """
        Runs atomic import for the given BulkImportJob.
        If rows_to_import is not provided, uses job.all_parsed_rows.
        Returns True on success, raises Exception on rollback.
        """
        if rows_to_import is None:
            rows_to_import = job.all_parsed_rows

        if not rows_to_import:
            job.status = BulkImportJob.Status.FAILED
            job.import_log = "No valid rows available to import."
            job.save()
            return False

        created_count = 0
        updated_count = 0
        skipped_count = 0

        try:
            with transaction.atomic():
                if job.import_type == BulkImportJob.ImportType.CURRICULUM:
                    created_count, updated_count, skipped_count = cls._import_curriculum(rows_to_import)

                elif job.import_type == BulkImportJob.ImportType.QUESTIONS:
                    created_count, updated_count, skipped_count = cls._import_questions(rows_to_import)

                elif job.import_type == BulkImportJob.ImportType.GAME_CONTENT:
                    created_count, updated_count, skipped_count = cls._import_game_content(rows_to_import)

                elif job.import_type == BulkImportJob.ImportType.QUIZZES:
                    created_count, updated_count, skipped_count = cls._import_quizzes(rows_to_import)

                else:
                    raise ValueError(f"Unknown import type: {job.import_type}")

                # If we reached here without errors, transaction commits!
                job.status = BulkImportJob.Status.IMPORTED
                job.created_count = created_count
                job.updated_count = updated_count
                job.duplicate_count = skipped_count
                job.import_log = (
                    f"Successfully imported {len(rows_to_import)} records: "
                    f"{created_count} created, {updated_count} updated, {skipped_count} skipped/duplicates."
                )
                job.save()
                return True

        except Exception as exc:
            logger.exception("Bulk import failed and rolled back for job %s: %s", job.job_id, exc)
            job.status = BulkImportJob.Status.ROLLED_BACK
            job.import_log = f"Transaction rolled back due to error: {str(exc)}"
            job.save()
            raise exc

    @classmethod
    def _import_curriculum(cls, rows: list) -> tuple:
        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            if row.get("action") == "DUPLICATE":
                skipped += 1
                continue

            grade_id = row["grade_id"]
            subject_id = row["subject_id"]
            ch_title = row["chapter_title"]
            c_title = row["concept_title"]

            # Topic (Chapter)
            topic, t_created = Topic.objects.get_or_create(
                grade_id=grade_id,
                subject_id=subject_id,
                title=ch_title,
                defaults={
                    "order": row.get("chapter_order", 0),
                    "difficulty": row.get("chapter_difficulty", "easy"),
                    "description": row.get("chapter_description", ""),
                    "status": "published",
                    "published_at": timezone.now()
                }
            )
            if not t_created and row.get("action") == "UPDATE":
                if row.get("chapter_order"):
                    topic.order = row["chapter_order"]
                if row.get("chapter_difficulty"):
                    topic.difficulty = row["chapter_difficulty"]
                if row.get("chapter_description"):
                    topic.description = row["chapter_description"]
                topic.save()

            # Concept
            concept, c_created = Concept.objects.get_or_create(
                topic=topic,
                title=c_title,
                defaults={
                    "order": row.get("concept_order", 0),
                    "content_body": row.get("concept_content", ""),
                    "status": "published",
                    "published_at": timezone.now()
                }
            )
            if not c_created and row.get("action") == "UPDATE":
                if row.get("concept_order"):
                    concept.order = row["concept_order"]
                if row.get("concept_content"):
                    concept.content_body = row["concept_content"]
                concept.save()
                updated += 1
            else:
                created += 1

        return created, updated, skipped

    @classmethod
    def _import_questions(cls, rows: list) -> tuple:
        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            action = row.get("action")
            if action == "DUPLICATE":
                skipped += 1
                continue

            topic_id = row["topic_id"]
            concept_id = row.get("concept_id")

            if action == "UPDATE" and row.get("question_id"):
                q = Question.objects.get(id=row["question_id"])
                q.topic_id = topic_id
                q.concept_id = concept_id
                q.prompt = row["prompt"]
                q.explanation = row.get("explanation", "")
                q.difficulty = row.get("difficulty", "easy")
                q.allow_multiple_answers = row.get("allow_multiple_answers", False)
                q.marks = row.get("marks", 1)
                q.negative_marks = row.get("negative_marks", 0)
                q.status = "published"
                q.published_at = timezone.now()
                q.save()

                # Replace options
                q.options.all().delete()
                for opt_info in row["options"]:
                    Option.objects.create(
                        question=q,
                        text=opt_info["text"],
                        is_correct=opt_info["is_correct"],
                        order=opt_info["order"]
                    )

                if row.get("hint"):
                    Hint.objects.filter(question=q).delete()
                    Hint.objects.create(question=q, text=row["hint"], order=1)

                updated += 1

            else:
                # CREATE
                q = Question.objects.create(
                    topic_id=topic_id,
                    concept_id=concept_id,
                    prompt=row["prompt"],
                    explanation=row.get("explanation", ""),
                    difficulty=row.get("difficulty", "easy"),
                    allow_multiple_answers=row.get("allow_multiple_answers", False),
                    marks=row.get("marks", 1),
                    negative_marks=row.get("negative_marks", 0),
                    status="published",
                    published_at=timezone.now()
                )

                for opt_info in row["options"]:
                    Option.objects.create(
                        question=q,
                        text=opt_info["text"],
                        is_correct=opt_info["is_correct"],
                        order=opt_info["order"]
                    )

                if row.get("hint"):
                    Hint.objects.create(question=q, text=row["hint"], order=1)

                created += 1

        return created, updated, skipped

    @classmethod
    def _import_game_content(cls, rows: list) -> tuple:
        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            action = row.get("action")
            if action == "DUPLICATE":
                skipped += 1
                continue

            game_id = row["game_id"]
            order = row["order"]

            gc, is_new = GameContent.objects.get_or_create(
                game_id=game_id,
                order=order,
                defaults={
                    "prompt": row.get("prompt", ""),
                    "content_type": row.get("content_type", "standard"),
                    "points": row.get("points", 10),
                    "data": row.get("data", {}),
                    "correct_answer": row.get("correct_answer"),
                    "hints": row.get("hints", [])
                }
            )

            if not is_new and action == "UPDATE":
                gc.prompt = row.get("prompt", "")
                gc.content_type = row.get("content_type", "standard")
                gc.points = row.get("points", 10)
                gc.data = row.get("data", {})
                gc.correct_answer = row.get("correct_answer")
                gc.hints = row.get("hints", [])
                gc.save()
                updated += 1
            else:
                created += 1

        return created, updated, skipped

    @classmethod
    def _import_quizzes(cls, rows: list) -> tuple:
        created = 0
        updated = 0
        skipped = 0

        # Group rows by quiz_title and topic
        quizzes_map = {}
        for row in rows:
            title = row["quiz_title"]
            topic_id = row["topic_id"]
            key = (topic_id, title)
            if key not in quizzes_map:
                quiz, _ = Quiz.objects.get_or_create(
                    topic_id=topic_id,
                    title=title,
                    defaults={
                        "duration_seconds": row.get("duration_seconds", 900),
                        "status": "published",
                        "published_at": timezone.now()
                    }
                )
                quizzes_map[key] = quiz

        # Import questions and link to quiz
        for idx, row in enumerate(rows):
            quiz = quizzes_map[(row["topic_id"], row["quiz_title"])]
            q_created, q_updated, q_skipped = cls._import_questions([row])
            created += q_created
            updated += q_updated
            skipped += q_skipped

            # Find question to link
            q = Question.objects.filter(topic_id=row["topic_id"], prompt=row["prompt"]).order_by("-id").first()
            if q:
                QuizQuestion.objects.get_or_create(
                    quiz=quiz,
                    question=q,
                    defaults={"order": idx + 1}
                )

        return created, updated, skipped
