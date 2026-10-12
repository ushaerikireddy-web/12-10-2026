from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from certificates.services import generate_certificate
from courses.models import Category, Course, Enrollment, Lesson, Module


class CertificateTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username='inst', email='i@e.com', password='pw12345678', role=User.Roles.INSTRUCTOR)
        self.student = User.objects.create_user(username='stud', email='s@e.com', password='pw12345678')
        cat = Category.objects.create(name='CS')
        self.course = Course.objects.create(title='C1', description='d', instructor=self.instructor, category=cat, status=Course.Status.PUBLISHED)
        mod = Module.objects.create(course=self.course, title='M', order=0)
        self.lesson = Lesson.objects.create(module=mod, title='L', video_url='https://example.com/v', order=0)

    def test_no_certificate_before_completion(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='stud', password='pw12345678')
        resp = self.client.post(reverse('certificates:certificate-generate', kwargs={'course_id': self.course.pk}))
        self.assertEqual(resp.status_code, 302)
        from certificates.models import Certificate
        self.assertFalse(Certificate.objects.filter(student=self.student, course=self.course).exists())

    def test_certificate_after_completion_no_duplicates(self):
        from courses.services import mark_lesson_complete
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        mark_lesson_complete(enrollment, self.lesson)
        cert1, created1 = generate_certificate(Enrollment.objects.get(pk=enrollment.pk))
        self.assertTrue(created1)
        cert2, created2 = generate_certificate(Enrollment.objects.get(pk=enrollment.pk))
        self.assertFalse(created2)
        self.assertEqual(cert1.pk, cert2.pk)
        self.assertTrue(cert1.pdf)
