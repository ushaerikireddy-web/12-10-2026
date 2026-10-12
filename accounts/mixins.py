"""Role-based access mixins. Superusers bypass all role checks."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic.base import View


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser:
            return View.dispatch(self, request, *args, **kwargs)
        if getattr(request.user, 'role', None) not in self.allowed_roles:
            raise PermissionDenied('You do not have permission to access this page.')
        return View.dispatch(self, request, *args, **kwargs)


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('STUDENT', 'INSTRUCTOR', 'ADMIN')


class StrictStudentMixin(RoleRequiredMixin):
    allowed_roles = ('STUDENT',)


class InstructorRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('INSTRUCTOR', 'ADMIN')


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ('ADMIN',)
