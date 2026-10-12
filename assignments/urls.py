from django.urls import path

from .views import (
    AssignmentCreateView,
    AssignmentDetailView,
    AssignmentListView,
    AssignmentUpdateView,
    SubmissionCreateView,
    SubmissionGradeView,
)

app_name = 'assignments'

urlpatterns = [
    path('', AssignmentListView.as_view(), name='assignment-list'),
    path('create/', AssignmentCreateView.as_view(), name='assignment-create'),
    path('<int:pk>/', AssignmentDetailView.as_view(), name='assignment-detail'),
    path('<int:pk>/edit/', AssignmentUpdateView.as_view(), name='assignment-edit'),
    path('<int:pk>/submit/', SubmissionCreateView.as_view(), name='submission-create'),
    path('submissions/<int:sub_id>/grade/', SubmissionGradeView.as_view(), name='submission-grade'),
]
