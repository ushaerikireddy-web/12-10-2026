"""DRF serializers + viewsets for Bootstrap JS frontend integration."""
import django_filters
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Category, Course


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class CourseSerializer(serializers.ModelSerializer):
    instructor = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'description', 'instructor', 'category',
                  'price', 'difficulty', 'status', 'created_at')


class CourseFilter(django_filters.FilterSet):
    class Meta:
        model = Course
        fields = {'category': ['exact'], 'difficulty': ['exact'], 'status': ['exact']}


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = CourseFilter
    search_fields = ('title', 'description')
    ordering_fields = ('created_at', 'price', 'title')
    lookup_field = 'slug'

    def get_queryset(self):
        if self.request.user.is_authenticated and getattr(self.request.user, 'is_instructor', False):
            return Course.objects.select_related('instructor', 'category').all()
        return Course.objects.filter(status=Course.Status.PUBLISHED).select_related('instructor', 'category')
