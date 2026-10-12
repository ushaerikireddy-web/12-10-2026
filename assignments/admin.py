from django.contrib import admin

from .models import Assignment, Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'is_published', 'due_date', 'max_marks', 'allow_late')
    list_filter = ('is_published', 'course', 'allow_late')
    search_fields = ('title', 'course__title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'marks', 'is_late', 'submitted_at')
    list_filter = ('status', 'is_late')
    search_fields = ('assignment__title', 'student__username', 'student__email')
    readonly_fields = ('submitted_at', 'updated_at', 'is_late')
