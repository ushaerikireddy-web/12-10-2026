from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from courses.models import Enrollment

from .models import Certificate
from .services import check_eligibility, generate_certificate


class MyCertificatesView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = 'certificates/certificate_list.html'
    context_object_name = 'certificates'

    def get_queryset(self):
        return Certificate.objects.filter(student=self.request.user).select_related('course')


class CertificateGenerateView(LoginRequiredMixin, View):
    def post(self, request, course_id):
        enrollment = get_object_or_404(Enrollment, student=request.user, course_id=course_id)
        try:
            check_eligibility(enrollment)
        except PermissionDenied as exc:
            messages.error(request, str(exc))
            return redirect('courses:course-detail', slug=enrollment.course.slug)
        cert, created = generate_certificate(enrollment)
        messages.success(request, f'Certificate {"issued" if created else "already exists"}: {cert.certificate_id}')
        return redirect('certificates:certificate-detail', pk=cert.pk)


class CertificateDetailView(LoginRequiredMixin, DetailView):
    model = Certificate
    template_name = 'certificates/certificate_detail.html'
    context_object_name = 'certificate'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Certificate, pk=self.kwargs['pk'])
        user = self.request.user
        if obj.student_id != user.id and not (user.is_superuser or getattr(user, 'role', '') == 'ADMIN'):
            if not (getattr(user, 'role', '') == 'INSTRUCTOR' and obj.course.instructor_id == user.id):
                raise PermissionDenied('Not your certificate.')
        return obj


class CertificateDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        cert = get_object_or_404(Certificate, pk=pk)
        user = request.user
        if cert.student_id != user.id and not (user.is_superuser or getattr(user, 'role', '') in ('ADMIN', 'INSTRUCTOR')):
            raise PermissionDenied('Not your certificate.')
        if not cert.pdf:
            raise Http404('PDF not available.')
        return FileResponse(cert.pdf.open('rb'), as_attachment=True, filename=f'certificate_{cert.certificate_id}.pdf')


class CertificateVerifyView(View):
    def get(self, request, certificate_id=None):
        if not certificate_id:
            return render(request, 'certificates/verify.html', {'certificate': None, 'query': ''})
        cert = Certificate.objects.filter(certificate_id__iexact=certificate_id.strip()).select_related('student', 'course').first()
        return render(request, 'certificates/verify.html', {'certificate': cert, 'query': certificate_id})

    def post(self, request):
        code = (request.POST.get('certificate_id') or '').strip()
        return redirect('certificates:certificate-verify-code', certificate_id=code or 'UNKNOWN')
