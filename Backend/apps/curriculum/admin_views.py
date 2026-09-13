from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from apps.curriculum.models import Subject, Topic, Concept


@staff_member_required
def curriculum_hierarchy_filter_api(request):
    """
    Server-side filtering API for Django Admin dependent selectors.
    Used by ConceptAdmin and GameAdmin.
    
    Query Params:
    - level='subjects'&grade_id=<int>  -> returns subjects belonging to grade
    - level='chapters'&grade_id=<int>&subject_id=<int> -> returns chapters matching grade+subject
    - level='concepts'&chapter_id=<int> -> returns concepts belonging to chapter
    """
    level = request.GET.get("level")

    if level == "subjects":
        grade_id = request.GET.get("grade_id")
        if not grade_id:
            return JsonResponse({"success": True, "data": []})
        subjects = Subject.objects.filter(topics__grade_id=grade_id).distinct().order_by("order", "name")
        data = [{"id": s.id, "name": s.name} for s in subjects]
        return JsonResponse({"success": True, "data": data})

    elif level == "chapters":
        grade_id = request.GET.get("grade_id")
        subject_id = request.GET.get("subject_id")
        if not grade_id or not subject_id:
            return JsonResponse({"success": True, "data": []})
        chapters = Topic.objects.filter(grade_id=grade_id, subject_id=subject_id).order_by("order", "title")
        data = [{"id": c.id, "title": f"Ch {c.order}: {c.title}" if c.order else c.title} for c in chapters]
        return JsonResponse({"success": True, "data": data})

    elif level == "concepts":
        chapter_id = request.GET.get("chapter_id")
        if not chapter_id:
            return JsonResponse({"success": True, "data": []})
        concepts = Concept.objects.filter(topic_id=chapter_id).order_by("order", "title")
        data = [{"id": cp.id, "title": f"{cp.order}. {cp.title}" if cp.order else cp.title} for cp in concepts]
        return JsonResponse({"success": True, "data": data})

    return JsonResponse({"success": False, "error": "Invalid level specified."}, status=400)
