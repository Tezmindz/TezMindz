"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from apps.curriculum.admin_views import curriculum_hierarchy_filter_api

urlpatterns = [
    path("admin/curriculum/hierarchy-filter/", curriculum_hierarchy_filter_api, name="admin_curriculum_hierarchy_filter"),
    path("admin/bulk-import/", include("apps.bulk_import.urls", namespace="bulk_import")),
    path("admin/", admin.site.urls),
    path("", include("common.urls")),
    path("api/curriculum/", include("apps.curriculum.urls")),
    path("api/quiz/", include("apps.assessments.api_urls")),
    path("games/", include("apps.games.urls")),
    path("api/game/", include("apps.games.api_urls")),
    path("api/games/", include("apps.games.api_urls")),
    path("api/auth/", include("apps.accounts.urls")),
    # Djoser user management (register, etc.)
    path("api/auth/", include("djoser.urls")),
    # New API modules
    path("api/progress/", include("apps.progress.urls")),
    path("api/gamification/", include("apps.gamification.urls")),
    path("api/subscriptions/", include("apps.subscriptions.urls")),
]
