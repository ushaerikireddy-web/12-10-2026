from django.urls import path

from .views import (
    CourseCreateView,
    CourseDeleteView,
    CourseDetailView,
    CourseListView,
    CourseUpdateView,
    EnrollView,
    LessonCompleteView,
    LessonCreateView,
    LessonDetailView,
    LessonUpdateView,
    ModuleCreateView,
    ModuleUpdateView,
)

app_name = 'courses'

urlpatterns = [
    path('', CourseListView.as_view(), name='course-list'),
    path('create/', CourseCreateView.as_view(), name='course-create'),
    path('<slug:slug>/', CourseDetailView.as_view(), name='course-detail'),
    path('<slug:slug>/edit/', CourseUpdateView.as_view(), name='course-edit'),
    path('<slug:slug>/delete/', CourseDeleteView.as_view(), name='course-delete'),
    path('<slug:slug>/enroll/', EnrollView.as_view(), name='course-enroll'),
    path('<slug:slug>/modules/add/', ModuleCreateView.as_view(), name='module-create'),
    path('<slug:slug>/modules/<int:module_id>/edit/', ModuleUpdateView.as_view(), name='module-edit'),
    path('<slug:slug>/modules/<int:module_id>/lessons/add/', LessonCreateView.as_view(), name='lesson-create'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/complete/', LessonCompleteView.as_view(), name='lesson-complete'),
    path('<slug:slug>/lessons/<int:pk>/edit/', LessonUpdateView.as_view(), name='lesson-edit'),
]
