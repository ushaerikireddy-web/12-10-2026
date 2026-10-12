from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core_validators import validate_document_file


class Assignment(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    attachment = models.FileField(upload_to='assignments/%Y/%m/', blank=True, null=True, validators=[validate_document_file])
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100, validators=[MinValueValidator(0)])
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    allow_late = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['course', 'is_published'])]

    def __str__(self):
        return f'{self.course.title} — {self.title}'

    @property
    def is_overdue(self):
        return bool(self.due_date and timezone.now() > self.due_date)


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        GRADED = 'GRADED', 'Graded'
        RETURNED = 'RETURNED', 'Returned for revision'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    answer_text = models.TextField(blank=True)
    file = models.FileField(upload_to='submissions/%Y/%m/', blank=True, null=True, validators=[validate_document_file])
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_late = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']
        indexes = [models.Index(fields=['assignment', 'status'])]

    def __str__(self):
        return f'{self.student.username} → {self.assignment.title}'

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if not self.answer_text.strip() and not self.file:
            raise ValidationError('Provide an answer text or upload a file.')
        if self.marks is not None and self.marks < 0:
            raise ValidationError('Marks cannot be negative.')
        if self.marks is not None and self.assignment_id and self.marks > self.assignment.max_marks:
            raise ValidationError(f'Marks cannot exceed {self.assignment.max_marks}.')

    def save(self, *args, **kwargs):
        if self.assignment_id and self.assignment.due_date:
            self.is_late = timezone.now() > self.assignment.due_date
        super().save(*args, **kwargs)
