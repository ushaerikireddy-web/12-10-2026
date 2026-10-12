from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from accounts.mixins import InstructorRequiredMixin
from assignments.models import Assignment

from .forms import CourseForm, LessonForm, ModuleForm
from .models import Course, Enrollment, Lesson, LessonProgress, Module
from .services import mark_lesson_complete, recalculate_enrollment_progress


class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9

    def get_queryset(self):
        qs = Course.objects.filter(status=Course.Status.PUBLISHED).select_related('instructor', 'category')
        # Instructors/admins browsing with ?mine=1 see their own courses incl. drafts
        user = self.request.user
        if self.request.GET.get('mine') and user.is_authenticated and getattr(user, 'is_instructor', False):
            qs = Course.objects.filter(instructor=user).select_related('instructor', 'category')
            if not (user.is_superuser or getattr(user, 'role', '') == 'ADMIN'):
                pass  # instructors see own drafts; published of others excluded via filter above? keep own only
            else:
                qs = Course.objects.all().select_related('instructor', 'category')
                if self.request.GET.get('mine'):
                    qs = qs.filter(instructor=user)
        q = self.request.GET.get('q', '').strip()
        cat = self.request.GET.get('category', '').strip()
        diff = self.request.GET.get('difficulty', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if cat:
            qs = qs.filter(category_id=cat)
        if diff:
            qs = qs.filter(difficulty=diff)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .forms import CourseSearchForm

        from .models import Category
        ctx['search_form'] = CourseSearchForm(self.request.GET or None)
        ctx['categories'] = Category.objects.all()
        if self.request.user.is_authenticated:
            enrolled_ids = set(Enrollment.objects.filter(student=self.request.user).values_list('course_id', flat=True))
            ctx['enrolled_ids'] = enrolled_ids
        return ctx


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') in ('INSTRUCTOR', 'ADMIN')):
            return Course.objects.select_related('instructor', 'category').prefetch_related('modules__lessons', 'assignments')
        return Course.objects.filter(status=Course.Status.PUBLISHED).select_related('instructor', 'category').prefetch_related('modules__lessons', 'assignments')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        enrollment = None
        completed_lesson_ids = set()
        if user.is_authenticated:
            enrollment = Enrollment.objects.filter(student=user, course=course).first()
            if enrollment:
                completed_lesson_ids = set(
                    LessonProgress.objects.filter(enrollment=enrollment, completed=True).values_list('lesson_id', flat=True)
                )
        ctx['enrollment'] = enrollment
        ctx['completed_lesson_ids'] = completed_lesson_ids
        ctx['is_owner'] = user.is_authenticated and (course.instructor_id == user.id or user.is_superuser or getattr(user, 'role', '') == 'ADMIN')
        ctx['published_assignments'] = course.assignments.filter(is_published=True)
        return ctx


class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, 'Course created.')
        return super().form_valid(form)


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Course.objects.all()
        return Course.objects.filter(instructor=user)

    def form_valid(self, form):
        messages.success(self.request, 'Course updated.')
        return super().form_valid(form)


class CourseDeleteView(InstructorRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course-list')
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Course.objects.all()
        return Course.objects.filter(instructor=user)


class EnrollView(LoginRequiredMixin, View):
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
        try:
            enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
        except IntegrityError:
            messages.warning(request, 'You are already enrolled in this course.')
            return redirect(course.get_absolute_url())
        if created:
            recalculate_enrollment_progress(enrollment)
            messages.success(request, f'Enrolled in "{course.title}".')
        else:
            messages.info(request, 'You are already enrolled in this course.')
        return redirect(course.get_absolute_url())


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'

    def get_object(self, queryset=None):
        lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=self.kwargs['pk'])
        course = lesson.course
        user = self.request.user
        # Owner / admin bypass enrollment
        if course.instructor_id == user.id or user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            self.enrollment = Enrollment.objects.filter(student=user, course=course).first()
            return lesson
        # Published courses require enrollment
        if course.status != Course.Status.PUBLISHED:
            raise PermissionDenied('Course is not published.')
        enrollment = Enrollment.objects.filter(student=user, course=course).first()
        if not enrollment:
            raise PermissionDenied('Enroll in the course to access lessons.')
        self.enrollment = enrollment
        return lesson

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lesson = self.object
        enrollment = getattr(self, 'enrollment', None)
        ctx['enrollment'] = enrollment
        ctx['course'] = lesson.course
        if enrollment:
            ctx['progress_record'] = LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).first()
            # prev/next within course
            lessons = list(Lesson.objects.filter(module__course=lesson.course).order_by('module__order', 'order', 'id'))
            ids = [l.id for l in lessons]
            idx = ids.index(lesson.id)
            ctx['prev_lesson'] = lessons[idx - 1] if idx > 0 else None
            ctx['next_lesson'] = lessons[idx + 1] if idx < len(lessons) - 1 else None
        return ctx


class LessonCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=pk)
        course = lesson.course
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if not enrollment:
            if course.instructor_id == request.user.id or request.user.is_superuser:
                messages.info(request, 'Instructors do not track progress on their own course.')
                return redirect('courses:lesson-detail', pk=lesson.pk)
            raise PermissionDenied('Enroll first.')
        position = int(request.POST.get('position', 0) or 0)
        record, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        record.last_position = max(0, position)
        record.save(update_fields=['last_position'])
        mark_lesson_complete(enrollment, lesson)
        messages.success(request, f'Marked "{lesson.title}" complete ({enrollment.progress}%).')
        return redirect('courses:lesson-detail', pk=lesson.pk)


# --- Module / Lesson management (instructor owns course) ---

class _OwnerCourseMixin(InstructorRequiredMixin):
    def get_course(self):
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        user = self.request.user
        if not (course.instructor_id == user.id or user.is_superuser or getattr(user, 'role', '') == 'ADMIN'):
            raise PermissionDenied('Only the course instructor can manage content.')
        return course


class ModuleCreateView(_OwnerCourseMixin, CreateView):
    form_class = ModuleForm
    template_name = 'courses/module_form.html'

    def form_valid(self, form):
        form.instance.course = self.get_course()
        messages.success(self.request, 'Module added.')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.course.get_absolute_url()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.get_course()
        return ctx


class ModuleUpdateView(_OwnerCourseMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    pk_url_kwarg = 'module_id'

    def get_queryset(self):
        return Module.objects.filter(course=self.get_course())

    def get_success_url(self):
        return self.object.course.get_absolute_url()


class LessonCreateView(_OwnerCourseMixin, CreateView):
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'

    def get_module(self):
        return get_object_or_404(Module, pk=self.kwargs['module_id'], course=self.get_course())

    def form_valid(self, form):
        form.instance.module = self.get_module()
        messages.success(self.request, 'Lesson added.')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.course.get_absolute_url()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.get_course()
        ctx['module'] = self.get_module()
        return ctx


class LessonUpdateView(_OwnerCourseMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Lesson.objects.filter(module__course=self.get_course())

    def get_success_url(self):
        return self.object.course.get_absolute_url()
