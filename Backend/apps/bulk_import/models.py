import uuid
from django.db import models
from django.conf import settings


class BulkImportJob(models.Model):
    class ImportType(models.TextChoices):
        CURRICULUM = "curriculum", "Curriculum Hierarchy"
        QUESTIONS = "questions", "Questions / Mock Test Bank"
        GAME_CONTENT = "game_content", "Game Content / Mechanics"
        QUIZZES = "quizzes", "Quizzes & Mock Tests"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Validation"
        VALIDATED = "validated", "Validated (Ready for Import)"
        IMPORTED = "imported", "Imported Successfully"
        FAILED = "failed", "Validation Failed (Errors Found)"
        ROLLED_BACK = "rolled_back", "Rolled Back"

    job_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    import_type = models.CharField(max_length=40, choices=ImportType.choices)
    filename = models.CharField(max_length=255)
    file_size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bulk_import_jobs"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)

    error_summary = models.JSONField(default=list, blank=True)
    preview_data = models.JSONField(default=list, blank=True)
    all_parsed_rows = models.JSONField(default=list, blank=True)
    import_log = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bulk Import Audit Log"
        verbose_name_plural = "Bulk Import Audit Logs"

    def __str__(self):
        return f"{self.get_import_type_display()} ({self.filename}) - {self.get_status_display()}"
