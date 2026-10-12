from django.contrib.auth.models import AbstractUser
from django.db import models

from core_validators import validate_image_file


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        ADMIN = 'ADMIN', 'Administrator'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT, db_index=True)
    email = models.EmailField(unique=True)

    REQUIRED_FIELDS = ['email']

    class Meta:
        indexes = [models.Index(fields=['role'])]

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_student(self):
        return self.role == self.Roles.STUDENT

    @property
    def is_instructor(self):
        return self.role in (self.Roles.INSTRUCTOR, self.Roles.ADMIN) or self.is_superuser

    @property
    def is_admin_user(self):
        return self.role == self.Roles.ADMIN or self.is_superuser


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='profiles/%Y/%m/', blank=True, null=True, validators=[validate_image_file])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.username}'

    def display_name(self):
        return self.full_name or self.user.get_full_name() or self.user.username
