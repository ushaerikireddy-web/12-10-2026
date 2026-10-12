from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Category, Course, Enrollment, Lesson, LessonProgress, Module
from courses.services import mark_lesson_complete, recalculate_enrollment_progress


def make_users():
    instructor = User.objects.create_user(username='inst', email='inst@e.com', password='pw12345678', role=User.Roles.INSTRUCTOR)
    student = User.objects.create_user(username='stud', email='stud@e.com', password='pw12345678', role=User.Roles.STUDENT)
    return instructor, student


def make_course(instructor):
    cat = Category.objects.create(name='Programming')
    course = Course.objects.create(title='Python 101', description='Intro', instructor=instructor,
                                   category=cat, status=Course.Status.PUBLISHED)
    mod = Module.objects.create(course=course, title='M1', order=0)
    Lesson.objects.create(module=mod, title='L1', video_url='https://example.com/v1', order=0)
    Lesson.objects.create(module=mod, title='L2', video_url='https://example.com/v2', order=1)
    return course


class CourseTests(TestCase):
    def test_duplicate_enrollment_prevented(self):
        instructor, student = make_users()
        course = make_course(instructor)
        e1, created1 = Enrollment.objects.get_or_create(student=student, course=course)
        self.assertTrue(created1)
        e2, created2 = Enrollment.objects.get_or_create(student=student, course=course)
        self.assertFalse(created2)
        self.assertEqual(Enrollment.objects.filter(student=student, course=course).count(), 1)

    def test_progress_and_completion(self):
        instructor, student = make_users()
        course = make_course(instructor)
        enrollment = Enrollment.objects.create(student=student, course=course)
        recalculate_enrollment_progress(enrollment)
        enrollment.refresh_from_db()
        self.assertEqual(float(enrollment.progress), 0)
        self.assertFalse(enrollment.completed)
        lessons = list(Lesson.objects.filter(module__course=course).order_by('order'))
        mark_lesson_complete(enrollment, lessons[0])
        enrollment.refresh_from_db()
        self.assertEqual(float(enrollment.progress), 50)
        mark_lesson_complete(enrollment, lessons[1])
        enrollment.refresh_from_db()
        self.assertEqual(float(enrollment.progress), 100)
        self.assertTrue(enrollment.completed)

    def test_unenrolled_cannot_view_lesson(self):
        instructor, student = make_users()
        course = make_course(instructor)
        lesson = Lesson.objects.filter(module__course=course).first()
        self.client.login(username='stud', password='pw12345678')
        resp = self.client.get(reverse('courses:lesson-detail', kwargs={'pk': lesson.pk}))
        self.assertEqual(resp.status_code, 403)
