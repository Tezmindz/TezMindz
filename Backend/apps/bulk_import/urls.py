from django.urls import path
from . import views

app_name = "bulk_import"

urlpatterns = [
    path("", views.bulk_import_hub, name="hub"),
    path("template/<str:import_type>/", views.download_template, name="download_template"),
    path("upload/<str:import_type>/", views.upload_view, name="upload"),
    path("preview/<uuid:job_id>/", views.preview_view, name="preview"),
    path("export-errors/<uuid:job_id>/", views.export_errors_view, name="export_errors"),
    path("confirm/<uuid:job_id>/", views.confirm_import_view, name="confirm"),
    path("success/<uuid:job_id>/", views.success_view, name="success"),
]
