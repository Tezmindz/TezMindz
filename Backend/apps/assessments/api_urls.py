from django.urls import path
from .api import (
    submit_quiz_attempt,
    mock_test_list_api,
    mock_test_detail_api,
    mock_test_submit_api
)

urlpatterns = [
    path("submit/", submit_quiz_attempt, name="submit_quiz_attempt"),
    path("mock-tests/", mock_test_list_api, name="mock_test_list_api"),
    path("mock-tests/<int:test_id>/", mock_test_detail_api, name="mock_test_detail_api"),
    path("mock-tests/<int:test_id>/submit/", mock_test_submit_api, name="mock_test_submit_api"),
]

