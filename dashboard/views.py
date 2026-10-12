from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.mixins import AdminRequiredMixin, InstructorRequiredMixin, StudentRequiredMixin
from assignments.models import Assignment, Submission
from certificates.models import Certificate
from courses.models import Course, Enrollment, LessonProgress
from pages.models import ContactMessage

User = get_user_model()


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get(self, request, *args, **kwargs):
        role = getattr(request.user, 'role', 'STUDENT')
        if request.user.is_superuser or role == 'ADMIN':
            return redirect('dashboard:admin')
        if role == 'INSTRUCTOR':
            return redirect('dashboard:instructor')
        return redirect('dashboard:student')


class StudentDashboardView(StudentRequiredMixin, TemplateView):
    template_name = 'dashboard/student.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__category').order_by('-enrolled_at')
        ctx['enrollments'] = enrollments
        ctx['completed_courses'] = enrollments.filter(completed=True)
        recent_progress = LessonProgress.objects.filter(enrollment__student=user).select_related(
            'lesson__module__course').order_by('-completed_at', '-id')[:10]
        ctx['recent_lessons'] = recent_progress
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        ctx['pending_assignments'] = Assignment.objects.filter(
            course_id__in=enrolled_course_ids, is_published=True).exclude(submissions__student=user).order_by('due_date')[:10]
        ctx['my_submissions'] = Submission.objects.filter(student=user).select_related('assignment__course').order_by('-submitted_at')[:10]
        ctx['certificates'] = Certificate.objects.filter(student=user).select_related('course')
        return ctx


class InstructorDashboardView(InstructorRequiredMixin, TemplateView):
    template_name = 'dashboard/instructor.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            courses = Course.objects.all()
        else:
            courses = Course.objects.filter(instructor=user)
        courses = courses.annotate(enrollment_count=Count('enrollments')).order_by('-created_at')
        ctx['courses'] = courses
        ctx['total_students'] = Enrollment.objects.filter(course__in=courses).values('student').distinct().count()
        ctx['pending_reviews'] = Submission.objects.filter(
            assignment__course__in=courses, status=Submission.Status.SUBMITTED).select_related('assignment', 'student')[:20]
        ctx['recent_submissions'] = Submission.objects.filter(assignment__course__in=courses).select_related('assignment', 'student').order_by('-submitted_at')[:10]
        ctx['avg_progress'] = Enrollment.objects.filter(course__in=courses).aggregate(avg=Avg('progress'))['avg'] or 0
        return ctx


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/admin.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = {
            'users': User.objects.count(),
            'students': User.objects.filter(role='STUDENT').count(),
            'instructors': User.objects.filter(role='INSTRUCTOR').count(),
            'courses': Course.objects.count(),
            'published_courses': Course.objects.filter(status=Course.Status.PUBLISHED).count(),
            'enrollments': Enrollment.objects.count(),
            'assignments': Assignment.objects.count(),
            'submissions': Submission.objects.count(),
            'certificates': Certificate.objects.count(),
            'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        }
        ctx['recent_enrollments'] = Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:10]
        ctx['recent_messages'] = ContactMessage.objects.order_by('-created_at')[:10]
        ctx['top_courses'] = Course.objects.annotate(n=Count('enrollments')).order_by('-n')[:5]
        return ctx
