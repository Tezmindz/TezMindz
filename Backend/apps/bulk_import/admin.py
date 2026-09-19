from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import BulkImportJob


@admin.register(BulkImportJob)
class BulkImportJobAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "import_type_badge",
        "status_badge",
        "total_rows",
        "valid_rows",
        "error_rows",
        "created_count",
        "updated_count",
        "uploaded_by",
        "created_at",
        "actions_column"
    )
    list_filter = ("import_type", "status", "created_at")
    search_fields = ("filename", "import_log", "uploaded_by__username")
    readonly_fields = (
        "job_id",
        "import_type",
        "filename",
        "file_size_bytes",
        "uploaded_by",
        "status",
        "total_rows",
        "valid_rows",
        "error_rows",
        "created_count",
        "updated_count",
        "duplicate_count",
        "error_summary",
        "preview_data",
        "all_parsed_rows",
        "import_log",
        "created_at",
        "updated_at"
    )
    ordering = ("-created_at",)

    @admin.display(description="Import Type")
    def import_type_badge(self, obj):
        colors = {
            "curriculum": "#4F46E5",
            "questions": "#059669",
            "game_content": "#D97706",
            "quizzes": "#7C3AED",
        }
        color = colors.get(obj.import_type, "#64748B")
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.75rem;">{}</span>',
            color,
            obj.get_import_type_display()
        )

    @admin.display(description="Status")
    def status_badge(self, obj):
        status_colors = {
            BulkImportJob.Status.IMPORTED: ("#ECFDF5", "#059669"),
            BulkImportJob.Status.VALIDATED: ("#EFF6FF", "#2563EB"),
            BulkImportJob.Status.FAILED: ("#FEF2F2", "#DC2626"),
            BulkImportJob.Status.ROLLED_BACK: ("#FFFBEB", "#D97706"),
            BulkImportJob.Status.PENDING: ("#F1F5F9", "#475569"),
        }
        bg, fg = status_colors.get(obj.status, ("#F1F5F9", "#475569"))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.75rem;">{}</span>',
            bg,
            fg,
            obj.get_status_display()
        )

    @admin.display(description="Actions")
    def actions_column(self, obj):
        preview_url = reverse("bulk_import:preview", kwargs={"job_id": obj.job_id})
        return format_html(
            '<a href="{}" style="padding: 3px 8px; background: #EEF2FF; color: #4F46E5; border-radius: 6px; font-weight: 700; text-decoration: none;">Inspect Preview</a>',
            preview_url
        )
