from django.test import TestCase
from django.urls import reverse

from .models import Profile, User


class AuthTests(TestCase):
    def test_student_registration(self):
        resp = self.client.post(reverse('accounts:register'), {
            'username': 'stud1', 'email': 'stud1@example.com',
            'password1': 'StrongPass123!', 'password2': 'StrongPass123!',
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='stud1')
        self.assertEqual(user.role, User.Roles.STUDENT)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_login_and_profile(self):
        User.objects.create_user(username='s', email='s@e.com', password='pw12345678')
        self.assertTrue(self.client.login(username='s', password='pw12345678'))
        resp = self.client.get(reverse('accounts:profile'))
        self.assertEqual(resp.status_code, 200)

    def test_role_mixin_denies_student_from_instructor_page(self):
        User.objects.create_user(username='s', email='s@e.com', password='pw12345678', role=User.Roles.STUDENT)
        self.client.login(username='s', password='pw12345678')
        resp = self.client.get(reverse('courses:course-create'))
        self.assertIn(resp.status_code, (302, 403))
