from django.urls import path

from .views import (
    CertificateDetailView,
    CertificateDownloadView,
    CertificateGenerateView,
    CertificateVerifyView,
    MyCertificatesView,
)

app_name = 'certificates'

urlpatterns = [
    path('', MyCertificatesView.as_view(), name='certificate-list'),
    path('generate/<int:course_id>/', CertificateGenerateView.as_view(), name='certificate-generate'),
    path('<int:pk>/', CertificateDetailView.as_view(), name='certificate-detail'),
    path('<int:pk>/download/', CertificateDownloadView.as_view(), name='certificate-download'),
    path('verify/', CertificateVerifyView.as_view(), name='certificate-verify'),
    path('verify/<str:certificate_id>/', CertificateVerifyView.as_view(), name='certificate-verify-code'),
]
