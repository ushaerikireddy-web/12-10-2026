"""DRF router for API endpoints (frontend JS/Bootstrap integration)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from courses.api import CategoryViewSet, CourseViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='api-category')
router.register(r'courses', CourseViewSet, basename='api-course')

urlpatterns = [
    path('', include(router.urls)),
]
