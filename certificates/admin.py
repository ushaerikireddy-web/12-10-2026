from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'student', 'course', 'instructor_name', 'issue_date')
    search_fields = ('certificate_id', 'student__username', 'student__email', 'course__title')
    list_filter = ('issue_date',)
    readonly_fields = ('certificate_id', 'issue_date')
