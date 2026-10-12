from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import InstructorRequiredMixin
from courses.models import Enrollment
from courses.services import recalculate_enrollment_progress

from .forms import AssignmentForm, GradingForm, SubmissionForm
from .models import Assignment, Submission


def _can_manage_assignment(user, assignment):
    return user.is_superuser or getattr(user, 'role', '') == 'ADMIN' or assignment.created_by_id == user.id or assignment.course.instructor_id == user.id


class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        course_id = self.request.GET.get('course')
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            qs = Assignment.objects.select_related('course').all()
        elif getattr(user, 'role', '') == 'INSTRUCTOR':
            qs = Assignment.objects.filter(course__instructor=user).select_related('course')
        else:
            enrolled = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
            qs = Assignment.objects.filter(course_id__in=enrolled, is_published=True).select_related('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs.order_by('-created_at')


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Assignment.objects.select_related('course'), pk=self.kwargs['pk'])
        user = self.request.user
        if _can_manage_assignment(user, obj):
            return obj
        if not obj.is_published:
            raise PermissionDenied('Assignment not published.')
        if not Enrollment.objects.filter(student=user, course=obj.course).exists():
            raise PermissionDenied('Enroll in the course to view assignments.')
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        assignment = self.object
        ctx['can_manage'] = _can_manage_assignment(user, assignment)
        ctx['my_submission'] = Submission.objects.filter(assignment=assignment, student=user).first()
        if ctx['can_manage']:
            ctx['submissions'] = assignment.submissions.select_related('student').all()
        return ctx


class AssignmentCreateView(InstructorRequiredMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'
    success_url = reverse_lazy('assignments:assignment-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        course = form.cleaned_data['course']
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'role', '') == 'ADMIN' or course.instructor_id == user.id):
            raise PermissionDenied('You can only create assignments for your own courses.')
        form.instance.created_by = user
        messages.success(self.request, 'Assignment created.')
        return super().form_valid(form)


class AssignmentUpdateView(InstructorRequiredMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Assignment.objects.all()
        return Assignment.objects.filter(course__instructor=user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Assignment updated.')
        return super().form_valid(form)


class SubmissionCreateView(LoginRequiredMixin, CreateView):
    model = Submission
    form_class = SubmissionForm
    template_name = 'assignments/submission_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(Assignment, pk=kwargs['pk'])
        if not self.assignment.is_published:
            raise PermissionDenied('Assignment not published.')
        if not Enrollment.objects.filter(student=request.user, course=self.assignment.course).exists():
            if not _can_manage_assignment(request.user, self.assignment):
                raise PermissionDenied('Enroll in the course to submit.')
        # Late policy
        if self.assignment.due_date and timezone.now() > self.assignment.due_date and not self.assignment.allow_late:
            messages.error(request, 'Deadline passed and late submissions are not allowed.')
            return redirect('assignments:assignment-detail', pk=self.assignment.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assignment'] = self.assignment
        ctx['existing'] = Submission.objects.filter(assignment=self.assignment, student=self.request.user).first()
        return ctx

    def form_valid(self, form):
        existing = Submission.objects.filter(assignment=self.assignment, student=self.request.user).first()
        if existing:
            # Allow resubmission before grading: update in place
            if existing.status == Submission.Status.GRADED:
                messages.error(self.request, 'Already graded; contact your instructor to resubmit.')
                return redirect('assignments:assignment-detail', pk=self.assignment.pk)
            existing.answer_text = form.cleaned_data['answer_text']
            if form.cleaned_data.get('file'):
                existing.file = form.cleaned_data['file']
            existing.status = Submission.Status.SUBMITTED
            existing.full_clean()
            existing.save()
            enrollment = Enrollment.objects.filter(student=self.request.user, course=self.assignment.course).first()
            if enrollment:
                recalculate_enrollment_progress(enrollment)
            messages.success(self.request, 'Submission updated.')
            return redirect('assignments:assignment-detail', pk=self.assignment.pk)
        form.instance.assignment = self.assignment
        form.instance.student = self.request.user
        response = super().form_valid(form)
        enrollment = Enrollment.objects.filter(student=self.request.user, course=self.assignment.course).first()
        if enrollment:
            recalculate_enrollment_progress(enrollment)
        messages.success(self.request, 'Submitted successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('assignments:assignment-detail', kwargs={'pk': self.assignment.pk})


class SubmissionGradeView(InstructorRequiredMixin, UpdateView):
    model = Submission
    form_class = GradingForm
    template_name = 'assignments/grade_form.html'
    pk_url_kwarg = 'sub_id'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Submission.objects.select_related('assignment__course')
        return Submission.objects.filter(assignment__course__instructor=user).select_related('assignment__course')

    def form_valid(self, form):
        if form.cleaned_data.get('marks') is not None:
            form.instance.status = Submission.Status.GRADED
        messages.success(self.request, 'Submission graded.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assignments:assignment-detail', kwargs={'pk': self.object.assignment_id})
