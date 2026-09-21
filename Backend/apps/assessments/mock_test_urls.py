from django.urls import path
from .api import mock_test_list_api, mock_test_detail_api, mock_test_submit_api

urlpatterns = [
    path("", mock_test_list_api, name="api_mock_test_list"),
    path("<int:test_id>/", mock_test_detail_api, name="api_mock_test_detail"),
    path("<int:test_id>/submit/", mock_test_submit_api, name="api_mock_test_submit"),
]
