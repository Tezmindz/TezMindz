import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from apps.bulk_import.models import BulkImportJob
from apps.bulk_import.services.excel_service import ExcelService
from apps.bulk_import.services.validators import ValidatorRegistry
from apps.bulk_import.services.import_engine import ImportEngine

logger = logging.getLogger("tezmindz.bulk_import")

IMPORT_META = {
    "curriculum": {
        "title": "Curriculum Hierarchy Import",
        "description": "Bulk import Grades, Subjects, Chapters (Topics), and Concepts in structured order.",
        "icon": "bi-compass-fill",
        "color": "indigo",
        "target_admin": "/admin/curriculum/topic/"
    },
    "questions": {
        "title": "Question Bank & Mock Test Questions",
        "description": "Bulk import Olympiad and assessment questions with multiple choice options, hints, and scoring.",
        "icon": "bi-patch-question-fill",
        "color": "emerald",
        "target_admin": "/admin/assessments/question/"
    },
    "game_content": {
        "title": "Game Content & Missions",
        "description": "Bulk import level challenges, mathematical targets, and interactive steps for Game Plugins.",
        "icon": "bi-controller",
        "color": "amber",
        "target_admin": "/admin/games/game/"
    },
    "quizzes": {
        "title": "Quizzes & Mock Tests",
        "description": "Bulk import full timed quizzes and automatically link questions to practice exams.",
        "icon": "bi-award-fill",
        "color": "purple",
        "target_admin": "/admin/assessments/quiz/"
    }
}


@staff_member_required
def bulk_import_hub(request):
    """
    Central Bulk Import Hub overview in Django Admin.
    """
    recent_jobs = BulkImportJob.objects.select_related("uploaded_by").order_by("-created_at")[:10]
    context = {
        "title": "Bulk Excel Import Hub",
        "workflows": IMPORT_META,
        "recent_jobs": recent_jobs,
        "site_header": "TezMindz Administration",
    }
    return render(request, "admin/bulk_import/hub.html", context)


@staff_member_required
def download_template(request, import_type: str):
    """
    Downloads the official styled .xlsx template for the given import type.
    """
    if import_type not in IMPORT_META:
        return HttpResponse("Invalid import type requested.", status=400)

    try:
        excel_stream = ExcelService.generate_template(import_type)
        filename = f"TezMindz_{import_type.title()}_Import_Template.xlsx"
        response = HttpResponse(
            excel_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as exc:
        logger.exception("Error generating template for %s: %s", import_type, exc)
        return HttpResponse(f"Error generating Excel template: {str(exc)}", status=500)


@staff_member_required
def upload_view(request, import_type: str):
    """
    Step 1: Upload Excel file & run comprehensive validation before preview.
    """
    if import_type not in IMPORT_META:
        return redirect("bulk_import:hub")

    meta = IMPORT_META[import_type]

    if request.method == "POST":
        uploaded_file = request.FILES.get("excel_file")
        is_valid, err_msg = ExcelService.validate_uploaded_file(uploaded_file)
        if not is_valid:
            messages.error(request, err_msg)
            return render(request, "admin/bulk_import/upload.html", {"meta": meta, "import_type": import_type})

        # Parse Excel sheet
        raw_headers, rows, parse_err = ExcelService.parse_sheet_rows(uploaded_file)
        if parse_err:
            messages.error(request, parse_err)
            return render(request, "admin/bulk_import/upload.html", {"meta": meta, "import_type": import_type})

        # Validate rows according to import type
        if import_type == "curriculum":
            valid_rows, errors, stats = ValidatorRegistry.validate_curriculum(raw_headers, rows)
        elif import_type == "questions":
            valid_rows, errors, stats = ValidatorRegistry.validate_questions(raw_headers, rows)
        elif import_type == "game_content":
            valid_rows, errors, stats = ValidatorRegistry.validate_game_content(raw_headers, rows)
        elif import_type == "quizzes":
            valid_rows, errors, stats = ValidatorRegistry.validate_quizzes(raw_headers, rows)
        else:
            return redirect("bulk_import:hub")

        job_status = BulkImportJob.Status.FAILED if errors else BulkImportJob.Status.VALIDATED

        # Persist session in BulkImportJob
        job = BulkImportJob.objects.create(
            import_type=import_type,
            filename=uploaded_file.name,
            file_size_bytes=uploaded_file.size,
            uploaded_by=request.user,
            status=job_status,
            total_rows=stats["total"],
            valid_rows=stats["valid"],
            error_rows=stats["errors"],
            created_count=stats["creates"],
            updated_count=stats["updates"],
            duplicate_count=stats["duplicates"],
            error_summary=errors,
            preview_data=valid_rows[:50],  # Preview first 50 rows
            all_parsed_rows=valid_rows
        )

        return redirect("bulk_import:preview", job_id=job.job_id)

    return render(request, "admin/bulk_import/upload.html", {
        "title": f"Upload {meta['title']}",
        "meta": meta,
        "import_type": import_type
    })


@staff_member_required
def preview_view(request, job_id):
    """
    Step 2: Interactive Preview UI with error drilldown and Confirm Import action.
    """
    job = get_object_or_404(BulkImportJob, job_id=job_id)
    meta = IMPORT_META.get(job.import_type, {})

    context = {
        "title": f"Import Preview - {job.filename}",
        "job": job,
        "meta": meta,
        "can_confirm": (job.error_rows == 0 and job.valid_rows > 0 and job.status == BulkImportJob.Status.VALIDATED),
    }
    return render(request, "admin/bulk_import/preview.html", context)


@staff_member_required
def export_errors_view(request, job_id):
    """
    Exports a downloadable .xlsx report of all errors found in the job.
    """
    job = get_object_or_404(BulkImportJob, job_id=job_id)
    if not job.error_summary:
        return HttpResponse("No errors recorded for this import job.", status=400)

    try:
        report_stream = ExcelService.generate_error_report(job)
        filename = f"Errors_{job.import_type}_{job.filename}.xlsx"
        response = HttpResponse(
            report_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as exc:
        logger.exception("Failed to export errors for job %s: %s", job_id, exc)
        return HttpResponse(f"Error generating report: {str(exc)}", status=500)


@staff_member_required
@require_POST
def confirm_import_view(request, job_id):
    """
    Step 3: Atomic database execution.
    """
    job = get_object_or_404(BulkImportJob, job_id=job_id)

    if job.status != BulkImportJob.Status.VALIDATED:
        messages.error(request, "This import job cannot be executed because it contains errors or has already been processed.")
        return redirect("bulk_import:preview", job_id=job.job_id)

    try:
        ImportEngine.execute_import(job)
        messages.success(request, f"Successfully imported {job.created_count + job.updated_count} records into the database!")
        return redirect("bulk_import:success", job_id=job.job_id)
    except Exception as exc:
        messages.error(request, f"Import failed and was rolled back: {str(exc)}")
        return redirect("bulk_import:preview", job_id=job.job_id)


@staff_member_required
def success_view(request, job_id):
    """
    Step 4: Success confirmation screen with direct links to the imported Django Admin list views.
    """
    job = get_object_or_404(BulkImportJob, job_id=job_id)
    meta = IMPORT_META.get(job.import_type, {})

    context = {
        "title": "Import Completed Successfully",
        "job": job,
        "meta": meta,
    }
    return render(request, "admin/bulk_import/success.html", context)
