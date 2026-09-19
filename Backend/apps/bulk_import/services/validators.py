import json
import re
from typing import Dict, List, Any, Tuple
from django.db.models import Q
from apps.curriculum.models import Grade, Subject, Topic, Concept
from apps.assessments.models import Question, Option, Quiz
from apps.games.models import Game, GameContent


def normalize_key(header: str) -> str:
    """Normalizes header string to snake_case identifier."""
    if not header:
        return ""
    h = header.strip().lower()
    h = re.sub(r"[\s\/\-\(\)\.]+", "_", h).strip("_")
    return h


HEADER_SYNONYMS = {
    # Curriculum
    "grade": ["grade", "class", "grade_class", "grade_level"],
    "subject": ["subject", "learning_world", "world"],
    "chapter": ["chapter", "topic", "chapter_topic", "chapter_title"],
    "concept": ["concept", "concept_title", "mission"],
    "chapter_order": ["chapter_order", "topic_order"],
    "chapter_difficulty": ["chapter_difficulty", "topic_difficulty"],
    "chapter_description": ["chapter_description", "topic_description", "chapter_desc"],
    "concept_order": ["concept_order", "order"],
    "concept_content": ["concept_content", "content_body", "content", "concept_description"],
    # Questions
    "prompt": ["question_prompt", "prompt", "question", "question_text"],
    "option_a": ["option_a", "option_1", "opt_a", "a"],
    "option_b": ["option_b", "option_2", "opt_b", "b"],
    "option_c": ["option_c", "option_3", "opt_c", "c"],
    "option_d": ["option_d", "option_4", "opt_d", "d"],
    "option_e": ["option_e", "option_5", "opt_e", "e"],
    "correct_answer": ["correct_answer", "correct", "answer", "correct_option", "key"],
    "difficulty": ["difficulty", "level"],
    "marks": ["marks", "mark", "points", "score"],
    "negative_marks": ["negative_marks", "neg_marks", "penalty"],
    "explanation": ["explanation", "solution", "rationale"],
    "allow_multiple_answers": ["allow_multiple_answers", "multiple_choice", "multiple_answers", "is_multi"],
    "hint_1": ["hint_1", "hint", "hints"],
    "question_id": ["question_id", "id", "qid", "external_id", "code"],
    # Game Content
    "game_title": ["game_title", "game", "title"],
    "step_order": ["step_order", "order", "step", "level"],
    "content_type": ["content_type", "type"],
    "data": ["target_data_json", "data", "data_json", "config"],
    "correct_answer_json": ["correct_answer_json", "correct_answer", "target"],
    "hints_json": ["hints_json", "hints"],
    # Quizzes
    "quiz_title": ["quiz_title", "quiz", "mock_test_title", "test_title"],
    "duration_minutes": ["quiz_duration_mins", "duration_mins", "duration_minutes", "duration", "time_limit"]
}


def canonicalize_row(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Maps arbitrary header variations in raw_row to canonical fields."""
    normalized_row = {}
    for raw_header, val in raw_row.items():
        norm = normalize_key(raw_header)
        matched_canonical = None
        for canonical, synonyms in HEADER_SYNONYMS.items():
            if norm in synonyms:
                matched_canonical = canonical
                break
        if matched_canonical:
            normalized_row[matched_canonical] = val
        else:
            normalized_row[norm] = val
    return normalized_row


class ValidatorRegistry:
    @staticmethod
    def validate_curriculum(raw_headers: List[str], rows: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Validates Curriculum rows (Grade, Subject, Chapter, Concept).
        Returns (valid_rows, error_list, stats).
        """
        # 1. Check required headers
        canonical_headers = set()
        for h in raw_headers:
            norm = normalize_key(h)
            for c_field, syns in HEADER_SYNONYMS.items():
                if norm in syns:
                    canonical_headers.add(c_field)

        required = ["grade", "subject", "chapter", "concept"]
        missing = [r for r in required if r not in canonical_headers]
        if missing:
            return [], [{
                "row": 1,
                "field": "Headers",
                "error": f"Missing required column headers: {', '.join(missing)}",
                "value": ""
            }], {"total": len(rows), "valid": 0, "errors": 1, "creates": 0, "updates": 0, "duplicates": 0}

        # Preload DB lookups for performance
        grades_cache = {g.name.strip().lower(): g for g in Grade.objects.all()}
        subjects_cache = {s.name.strip().lower(): s for s in Subject.objects.all()}
        # Also map integer strings like '5' to 'Class 5' or order=5
        for g in Grade.objects.all():
            grades_cache[str(g.order)] = g
            grades_cache[f"grade {g.order}"] = g
            grades_cache[f"class {g.order}"] = g

        topics_cache = {}
        for t in Topic.objects.select_related("grade", "subject").all():
            key = (t.grade_id, t.subject_id, t.title.strip().lower())
            topics_cache[key] = t

        concepts_cache = {}
        for c in Concept.objects.select_related("topic").all():
            key = (c.topic_id, c.title.strip().lower())
            concepts_cache[key] = c

        valid_rows = []
        errors = []
        creates = 0
        updates = 0
        duplicates = 0

        # Track seen in current batch to handle duplicates within the same sheet
        seen_in_batch = set()

        for item in rows:
            row_num = item["row_number"]
            row = canonicalize_row(item["data"])

            raw_grade = str(row.get("grade") or "").strip()
            raw_subject = str(row.get("subject") or "").strip()
            raw_chapter = str(row.get("chapter") or "").strip()
            raw_concept = str(row.get("concept") or "").strip()

            row_errors = []

            # 1. Field presence
            if not raw_grade:
                row_errors.append({"row": row_num, "field": "Grade", "error": "Grade cannot be blank.", "value": ""})
            if not raw_subject:
                row_errors.append({"row": row_num, "field": "Subject", "error": "Subject cannot be blank.", "value": ""})
            if not raw_chapter:
                row_errors.append({"row": row_num, "field": "Chapter", "error": "Chapter cannot be blank.", "value": ""})
            if not raw_concept:
                row_errors.append({"row": row_num, "field": "Concept", "error": "Concept cannot be blank.", "value": ""})

            if row_errors:
                errors.extend(row_errors)
                continue

            # 2. Grade validation
            grade_obj = grades_cache.get(raw_grade.lower())
            if not grade_obj:
                errors.append({
                    "row": row_num, "field": "Grade",
                    "error": f"Grade '{raw_grade}' does not exist in the database. Please create it first in Admin or check spelling.",
                    "value": raw_grade
                })
                continue

            # 3. Subject validation
            subject_obj = subjects_cache.get(raw_subject.lower())
            if not subject_obj:
                errors.append({
                    "row": row_num, "field": "Subject",
                    "error": f"Subject '{raw_subject}' does not exist in the database. Please create it first in Admin or check spelling.",
                    "value": raw_subject
                })
                continue

            # 4. Chapter (Topic) relationship check
            # Check if chapter title exists in another Grade or Subject
            existing_diff_topic = Topic.objects.filter(title__iexact=raw_chapter).exclude(grade=grade_obj, subject=subject_obj).first()
            # It's allowed for different grades to have same topic name, but if they intended it to be under this grade, verify it
            topic_key = (grade_obj.id, subject_obj.id, raw_chapter.lower())
            topic_obj = topics_cache.get(topic_key)

            # 5. Concept relationship check
            # If Concept exists under a DIFFERENT chapter, report relationship mismatch
            existing_diff_concept = Concept.objects.filter(title__iexact=raw_concept).select_related("topic", "topic__grade", "topic__subject").first()
            if existing_diff_concept and topic_obj and existing_diff_concept.topic_id != topic_obj.id:
                errors.append({
                    "row": row_num, "field": "Concept",
                    "error": f"Concept '{raw_concept}' is already linked to chapter '{existing_diff_concept.topic.title}' ({existing_diff_concept.topic.grade}), not '{raw_chapter}'.",
                    "value": raw_concept
                })
                continue

            # Batch duplicate check
            batch_key = (grade_obj.id, subject_obj.id, raw_chapter.lower(), raw_concept.lower())
            if batch_key in seen_in_batch:
                action = "DUPLICATE"
                duplicates += 1
            else:
                seen_in_batch.add(batch_key)
                if topic_obj:
                    concept_key = (topic_obj.id, raw_concept.lower())
                    concept_obj = concepts_cache.get(concept_key)
                    if concept_obj:
                        action = "UPDATE"
                        updates += 1
                    else:
                        action = "CREATE"
                        creates += 1
                else:
                    action = "CREATE"
                    creates += 1

            # Optional fields parsing
            chapter_order = 0
            try:
                if row.get("chapter_order"):
                    chapter_order = int(row["chapter_order"])
            except (ValueError, TypeError):
                pass

            concept_order = 0
            try:
                if row.get("concept_order"):
                    concept_order = int(row["concept_order"])
            except (ValueError, TypeError):
                pass

            raw_diff = str(row.get("chapter_difficulty") or "easy").strip().lower()
            diff_choices = ["easy", "medium", "hard"]
            difficulty = raw_diff if raw_diff in diff_choices else "easy"

            valid_rows.append({
                "row_number": row_num,
                "action": action,
                "grade_id": grade_obj.id,
                "grade_name": grade_obj.name,
                "subject_id": subject_obj.id,
                "subject_name": subject_obj.name,
                "chapter_title": raw_chapter,
                "chapter_order": chapter_order,
                "chapter_difficulty": difficulty,
                "chapter_description": str(row.get("chapter_description") or "").strip(),
                "concept_title": raw_concept,
                "concept_order": concept_order,
                "concept_content": str(row.get("concept_content") or "").strip() or f"Learn about {raw_concept}."
            })

        stats = {
            "total": len(rows),
            "valid": len(valid_rows),
            "errors": len(errors),
            "creates": creates,
            "updates": updates,
            "duplicates": duplicates
        }
        return valid_rows, errors, stats

    @staticmethod
    def validate_questions(raw_headers: List[str], rows: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Validates Question Bank / Mock Test rows.
        Returns (valid_rows, error_list, stats).
        """
        canonical_headers = set()
        for h in raw_headers:
            norm = normalize_key(h)
            for c_field, syns in HEADER_SYNONYMS.items():
                if norm in syns:
                    canonical_headers.add(c_field)

        required = ["grade", "subject", "chapter", "prompt", "option_a", "option_b", "correct_answer"]
        missing = [r for r in required if r not in canonical_headers]
        if missing:
            return [], [{
                "row": 1,
                "field": "Headers",
                "error": f"Missing required column headers: {', '.join(missing)}",
                "value": ""
            }], {"total": len(rows), "valid": 0, "errors": 1, "creates": 0, "updates": 0, "duplicates": 0}

        grades_cache = {g.name.strip().lower(): g for g in Grade.objects.all()}
        for g in Grade.objects.all():
            grades_cache[str(g.order)] = g
            grades_cache[f"class {g.order}"] = g
            grades_cache[f"grade {g.order}"] = g

        subjects_cache = {s.name.strip().lower(): s for s in Subject.objects.all()}

        topics_cache = {}
        for t in Topic.objects.select_related("grade", "subject").all():
            key = (t.grade_id, t.subject_id, t.title.strip().lower())
            topics_cache[key] = t

        concepts_cache = {}
        for c in Concept.objects.select_related("topic").all():
            key = (c.topic_id, c.title.strip().lower())
            concepts_cache[key] = c

        questions_by_id = {q.id: q for q in Question.objects.all()}
        questions_by_topic_prompt = {}
        for q in Question.objects.all():
            key = (q.topic_id, q.prompt.strip().lower())
            questions_by_topic_prompt[key] = q

        valid_rows = []
        errors = []
        creates = 0
        updates = 0
        duplicates = 0
        seen_batch_prompts = set()

        for item in rows:
            row_num = item["row_number"]
            row = canonicalize_row(item["data"])

            raw_grade = str(row.get("grade") or "").strip()
            raw_subject = str(row.get("subject") or "").strip()
            raw_chapter = str(row.get("chapter") or "").strip()
            raw_concept = str(row.get("concept") or "").strip()
            raw_prompt = str(row.get("prompt") or "").strip()
            raw_opt_a = str(row.get("option_a") or "").strip()
            raw_opt_b = str(row.get("option_b") or "").strip()
            raw_opt_c = str(row.get("option_c") or "").strip()
            raw_opt_d = str(row.get("option_d") or "").strip()
            raw_correct = str(row.get("correct_answer") or "").strip()

            row_errors = []

            if not raw_grade:
                row_errors.append({"row": row_num, "field": "Grade", "error": "Grade cannot be blank.", "value": ""})
            if not raw_subject:
                row_errors.append({"row": row_num, "field": "Subject", "error": "Subject cannot be blank.", "value": ""})
            if not raw_chapter:
                row_errors.append({"row": row_num, "field": "Chapter", "error": "Chapter cannot be blank.", "value": ""})
            if not raw_prompt:
                row_errors.append({"row": row_num, "field": "Question Prompt", "error": "Question Prompt cannot be blank.", "value": ""})
            if not raw_opt_a:
                row_errors.append({"row": row_num, "field": "Option A", "error": "Option A is required.", "value": ""})
            if not raw_opt_b:
                row_errors.append({"row": row_num, "field": "Option B", "error": "Option B is required.", "value": ""})
            if not raw_correct:
                row_errors.append({"row": row_num, "field": "Correct Answer", "error": "Correct Answer is required.", "value": ""})

            if row_errors:
                errors.extend(row_errors)
                continue

            # Hierarchy lookup
            grade_obj = grades_cache.get(raw_grade.lower())
            if not grade_obj:
                errors.append({
                    "row": row_num, "field": "Grade",
                    "error": f"Grade '{raw_grade}' does not exist in the database.",
                    "value": raw_grade
                })
                continue

            subject_obj = subjects_cache.get(raw_subject.lower())
            if not subject_obj:
                errors.append({
                    "row": row_num, "field": "Subject",
                    "error": f"Subject '{raw_subject}' does not exist in the database.",
                    "value": raw_subject
                })
                continue

            topic_key = (grade_obj.id, subject_obj.id, raw_chapter.lower())
            topic_obj = topics_cache.get(topic_key)
            if not topic_obj:
                # Check if chapter exists under a different Grade/Subject
                other_topic = Topic.objects.filter(title__iexact=raw_chapter).first()
                if other_topic:
                    errors.append({
                        "row": row_num, "field": "Chapter",
                        "error": f"Chapter '{raw_chapter}' belongs to {other_topic.grade.name} · {other_topic.subject.name}, not {grade_obj.name} · {subject_obj.name}.",
                        "value": raw_chapter
                    })
                else:
                    errors.append({
                        "row": row_num, "field": "Chapter",
                        "error": f"Chapter '{raw_chapter}' does not exist under Grade '{grade_obj.name}' and Subject '{subject_obj.name}'.",
                        "value": raw_chapter
                    })
                continue

            # Concept relationship check (optional)
            concept_obj = None
            if raw_concept:
                concept_key = (topic_obj.id, raw_concept.lower())
                concept_obj = concepts_cache.get(concept_key)
                if not concept_obj:
                    # Check if concept belongs to another chapter
                    other_concept = Concept.objects.filter(title__iexact=raw_concept).select_related("topic").first()
                    if other_concept:
                        errors.append({
                            "row": row_num, "field": "Concept",
                            "error": f"Concept '{raw_concept}' belongs to chapter '{other_concept.topic.title}', not '{topic_obj.title}'.",
                            "value": raw_concept
                        })
                    else:
                        errors.append({
                            "row": row_num, "field": "Concept",
                            "error": f"Concept '{raw_concept}' does not exist under chapter '{topic_obj.title}'.",
                            "value": raw_concept
                        })
                    continue

            # Options and Correct Answer validation
            options_dict = {"A": raw_opt_a, "B": raw_opt_b}
            if raw_opt_c:
                options_dict["C"] = raw_opt_c
            if raw_opt_d:
                options_dict["D"] = raw_opt_d
            raw_opt_e = str(row.get("option_e") or "").strip()
            if raw_opt_e:
                options_dict["E"] = raw_opt_e

            # Match correct answer: can be 'A', 'B', 'C', 'D' OR exact option text
            correct_keys = []
            clean_correct = raw_correct.strip()
            upper_correct = clean_correct.upper()

            # Handle comma-separated multiple answers if allowed
            raw_multi = str(row.get("allow_multiple_answers") or "").strip().lower()
            allow_multiple = raw_multi in ["true", "1", "yes", "y"]

            tokens = [t.strip() for t in clean_correct.replace(";", ",").split(",") if t.strip()]
            for token in tokens:
                token_upper = token.upper()
                if token_upper in options_dict:
                    correct_keys.append(token_upper)
                else:
                    # Match by text
                    matched = False
                    for opt_letter, opt_text in options_dict.items():
                        if opt_text.strip().lower() == token.lower():
                            correct_keys.append(opt_letter)
                            matched = True
                            break
                    if not matched:
                        errors.append({
                            "row": row_num, "field": "Correct Answer",
                            "error": f"Correct Answer '{token}' does not match any provided options ({', '.join(options_dict.keys())}).",
                            "value": raw_correct
                        })
                        break

            if len(errors) > 0 and errors[-1]["row"] == row_num:
                continue

            if not correct_keys:
                errors.append({
                    "row": row_num, "field": "Correct Answer",
                    "error": f"No valid correct option matched for '{raw_correct}'.",
                    "value": raw_correct
                })
                continue

            if not allow_multiple and len(correct_keys) > 1:
                errors.append({
                    "row": row_num, "field": "Correct Answer",
                    "error": f"Multiple correct answers specified ({', '.join(correct_keys)}), but 'Allow Multiple Answers' is FALSE.",
                    "value": raw_correct
                })
                continue

            # Parse numbers and settings
            try:
                marks = int(row.get("marks") or 1)
                if marks < 0:
                    marks = 1
            except (ValueError, TypeError):
                marks = 1

            try:
                neg_marks = int(row.get("negative_marks") or 0)
                if neg_marks < 0:
                    neg_marks = 0
            except (ValueError, TypeError):
                neg_marks = 0

            raw_diff = str(row.get("difficulty") or "easy").strip().lower()
            difficulty = raw_diff if raw_diff in ["easy", "medium", "hard"] else "easy"

            # Create / Update / Duplicate logic
            qid = row.get("question_id")
            action = "CREATE"
            matched_question_id = None

            if qid:
                try:
                    qid_int = int(qid)
                    if qid_int in questions_by_id:
                        action = "UPDATE"
                        matched_question_id = qid_int
                        updates += 1
                    else:
                        errors.append({
                            "row": row_num, "field": "Question ID",
                            "error": f"Question with ID '{qid}' not found for update.",
                            "value": qid
                        })
                        continue
                except (ValueError, TypeError):
                    errors.append({
                        "row": row_num, "field": "Question ID",
                        "error": f"Invalid integer Question ID '{qid}'.",
                        "value": qid
                    })
                    continue
            else:
                prompt_key = (topic_obj.id, raw_prompt.lower())
                if prompt_key in seen_batch_prompts:
                    action = "DUPLICATE"
                    duplicates += 1
                elif prompt_key in questions_by_topic_prompt:
                    action = "DUPLICATE"
                    matched_question_id = questions_by_topic_prompt[prompt_key].id
                    duplicates += 1
                else:
                    action = "CREATE"
                    creates += 1
                seen_batch_prompts.add(prompt_key)

            valid_rows.append({
                "row_number": row_num,
                "action": action,
                "question_id": matched_question_id,
                "topic_id": topic_obj.id,
                "concept_id": concept_obj.id if concept_obj else None,
                "prompt": raw_prompt,
                "explanation": str(row.get("explanation") or "").strip(),
                "difficulty": difficulty,
                "allow_multiple_answers": allow_multiple,
                "marks": marks,
                "negative_marks": neg_marks,
                "options": [{"text": txt, "is_correct": (letter in correct_keys), "order": idx + 1}
                            for idx, (letter, txt) in enumerate(options_dict.items())],
                "hint": str(row.get("hint_1") or "").strip()
            })

        stats = {
            "total": len(rows),
            "valid": len(valid_rows),
            "errors": len(errors),
            "creates": creates,
            "updates": updates,
            "duplicates": duplicates
        }
        return valid_rows, errors, stats

    @staticmethod
    def validate_game_content(raw_headers: List[str], rows: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Validates Game Content rows.
        Returns (valid_rows, error_list, stats).
        """
        canonical_headers = set()
        for h in raw_headers:
            norm = normalize_key(h)
            for c_field, syns in HEADER_SYNONYMS.items():
                if norm in syns:
                    canonical_headers.add(c_field)

        required = ["game_title", "step_order", "prompt"]
        missing = [r for r in required if r not in canonical_headers]
        if missing:
            return [], [{
                "row": 1,
                "field": "Headers",
                "error": f"Missing required column headers: {', '.join(missing)}",
                "value": ""
            }], {"total": len(rows), "valid": 0, "errors": 1, "creates": 0, "updates": 0, "duplicates": 0}

        games_cache = {g.title.strip().lower(): g for g in Game.objects.all()}
        content_cache = {}
        for gc in GameContent.objects.all():
            content_cache[(gc.game_id, gc.order)] = gc

        valid_rows = []
        errors = []
        creates = 0
        updates = 0
        duplicates = 0
        seen_batch = set()

        for item in rows:
            row_num = item["row_number"]
            row = canonicalize_row(item["data"])

            raw_game = str(row.get("game_title") or "").strip()
            raw_order = row.get("step_order")
            raw_prompt = str(row.get("prompt") or "").strip()

            if not raw_game:
                errors.append({"row": row_num, "field": "Game Title", "error": "Game Title cannot be blank.", "value": ""})
                continue
            if raw_order is None or str(raw_order).strip() == "":
                errors.append({"row": row_num, "field": "Step Order", "error": "Step Order cannot be blank.", "value": ""})
                continue

            try:
                order_int = int(raw_order)
                if order_int < 1:
                    raise ValueError
            except (ValueError, TypeError):
                errors.append({"row": row_num, "field": "Step Order", "error": f"Step Order must be a positive integer, got '{raw_order}'.", "value": str(raw_order)})
                continue

            game_obj = games_cache.get(raw_game.lower())
            if not game_obj:
                errors.append({
                    "row": row_num, "field": "Game Title",
                    "error": f"Game '{raw_game}' does not exist in the database. Please create the Game first in Game Library.",
                    "value": raw_game
                })
                continue

            # Validate JSON fields if present
            raw_data = row.get("data")
            parsed_data = {}
            if raw_data is not None and str(raw_data).strip() != "":
                if isinstance(raw_data, dict):
                    parsed_data = raw_data
                else:
                    try:
                        parsed_data = json.loads(str(raw_data))
                    except json.JSONDecodeError:
                        errors.append({
                            "row": row_num, "field": "Target Data (JSON)",
                            "error": f"Invalid JSON syntax in Target Data: {raw_data}",
                            "value": str(raw_data)
                        })
                        continue

            raw_correct = row.get("correct_answer_json")
            parsed_correct = None
            if raw_correct is not None and str(raw_correct).strip() != "":
                if isinstance(raw_correct, (dict, list, int, float, bool)):
                    parsed_correct = raw_correct
                else:
                    try:
                        parsed_correct = json.loads(str(raw_correct))
                    except json.JSONDecodeError:
                        # Allow plain string as answer
                        parsed_correct = str(raw_correct).strip()

            raw_hints = row.get("hints_json")
            parsed_hints = []
            if raw_hints is not None and str(raw_hints).strip() != "":
                if isinstance(raw_hints, list):
                    parsed_hints = raw_hints
                else:
                    try:
                        val = json.loads(str(raw_hints))
                        parsed_hints = val if isinstance(val, list) else [val]
                    except json.JSONDecodeError:
                        parsed_hints = [str(raw_hints).strip()]

            points = 10
            try:
                if row.get("points"):
                    points = int(row["points"])
            except (ValueError, TypeError):
                pass

            batch_key = (game_obj.id, order_int)
            if batch_key in seen_batch:
                action = "DUPLICATE"
                duplicates += 1
            else:
                seen_batch.add(batch_key)
                if batch_key in content_cache:
                    action = "UPDATE"
                    updates += 1
                else:
                    action = "CREATE"
                    creates += 1

            valid_rows.append({
                "row_number": row_num,
                "action": action,
                "game_id": game_obj.id,
                "game_title": game_obj.title,
                "order": order_int,
                "prompt": raw_prompt,
                "content_type": str(row.get("content_type") or "standard").strip(),
                "points": points,
                "data": parsed_data,
                "correct_answer": parsed_correct,
                "hints": parsed_hints
            })

        stats = {
            "total": len(rows),
            "valid": len(valid_rows),
            "errors": len(errors),
            "creates": creates,
            "updates": updates,
            "duplicates": duplicates
        }
        return valid_rows, errors, stats

    @staticmethod
    def validate_quizzes(raw_headers: List[str], rows: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Validates Quizzes & Mock Test questions.
        """
        canonical_headers = set()
        for h in raw_headers:
            norm = normalize_key(h)
            for c_field, syns in HEADER_SYNONYMS.items():
                if norm in syns:
                    canonical_headers.add(c_field)

        required = ["quiz_title", "grade", "subject", "chapter", "prompt", "option_a", "option_b", "correct_answer"]
        missing = [r for r in required if r not in canonical_headers]
        if missing:
            return [], [{
                "row": 1,
                "field": "Headers",
                "error": f"Missing required column headers: {', '.join(missing)}",
                "value": ""
            }], {"total": len(rows), "valid": 0, "errors": 1, "creates": 0, "updates": 0, "duplicates": 0}

        # Reuse questions validator logic with quiz assignment
        q_valid, errors, stats = ValidatorRegistry.validate_questions(raw_headers, rows)
        if errors:
            return q_valid, errors, stats

        # Attach quiz details to each row
        quizzes_cache = {q.title.strip().lower(): q for q in Quiz.objects.all()}
        for idx, item in enumerate(rows):
            row = canonicalize_row(item["data"])
            quiz_title = str(row.get("quiz_title") or "").strip()
            if not quiz_title:
                errors.append({
                    "row": item["row_number"], "field": "Quiz Title",
                    "error": "Quiz Title cannot be blank.", "value": ""
                })
                continue

            duration_mins = 15
            try:
                if row.get("duration_minutes"):
                    duration_mins = int(row["duration_minutes"])
            except (ValueError, TypeError):
                pass

            q_valid[idx]["quiz_title"] = quiz_title
            q_valid[idx]["duration_seconds"] = duration_mins * 60

        stats["errors"] = len(errors)
        stats["valid"] = len(q_valid) if not errors else 0
        return q_valid, errors, stats
