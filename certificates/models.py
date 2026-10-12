import uuid

from django.conf import settings
from django.db import models


def _cert_id():
    return uuid.uuid4().hex[:12].upper()


class Certificate(models.Model):
    certificate_id = models.CharField(max_length=16, unique=True, default=_cert_id, db_index=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='certificates')
    instructor_name = models.CharField(max_length=150, blank=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to='certificates/%Y/%m/', blank=True, null=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-issue_date']
        indexes = [models.Index(fields=['student', 'course'])]

    def __str__(self):
        return f'{self.certificate_id} — {self.student} / {self.course}'
