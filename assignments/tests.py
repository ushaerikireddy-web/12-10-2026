from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from assignments.models import Assignment, Submission
from courses.models import Category, Course, Enrollment


class AssignmentTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username='inst', email='i@e.com', password='pw12345678', role=User.Roles.INSTRUCTOR)
        self.student = User.objects.create_user(username='stud', email='s@e.com', password='pw12345678')
        self.other = User.objects.create_user(username='other', email='o@e.com', password='pw12345678')
        cat = Category.objects.create(name='Math')
        self.course = Course.objects.create(title='Algebra', description='d', instructor=self.instructor, category=cat, status=Course.Status.PUBLISHED)
        Enrollment.objects.create(student=self.student, course=self.course)
        self.assignment = Assignment.objects.create(
            course=self.course, title='HW1', instructions='Solve', created_by=self.instructor,
            is_published=True, due_date=timezone.now() + timezone.timedelta(days=1))

    def test_student_can_submit(self):
        self.client.login(username='stud', password='pw12345678')
        resp = self.client.post(reverse('assignments:submission-create', kwargs={'pk': self.assignment.pk}),
                                {'answer_text': '42'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Submission.objects.filter(assignment=self.assignment, student=self.student).exists())

    def test_other_student_cannot_view_submission(self):
        Submission.objects.create(assignment=self.assignment, student=self.student, answer_text='secret')
        self.client.login(username='other', password='pw12345678')
        # Other student not enrolled -> assignment detail denied
        resp = self.client.get(reverse('assignments:assignment-detail', kwargs={'pk': self.assignment.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_instructor_can_grade(self):
        sub = Submission.objects.create(assignment=self.assignment, student=self.student, answer_text='a')
        self.client.login(username='inst', password='pw12345678')
        resp = self.client.post(reverse('assignments:submission-grade', kwargs={'sub_id': sub.pk}),
                                {'marks': '85', 'feedback': 'Good', 'status': 'GRADED'})
        self.assertEqual(resp.status_code, 302)
        sub.refresh_from_db()
        self.assertEqual(float(sub.marks), 85)
