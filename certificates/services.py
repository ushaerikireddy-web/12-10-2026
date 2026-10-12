"""Certificate eligibility + PDF rendering with reportlab."""
import io
import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile


def check_eligibility(enrollment):
    """Raise PermissionDenied unless the enrollment meets completion requirements."""
    if not enrollment.completed or float(enrollment.progress) < 100:
        raise PermissionDenied('Complete all lessons and assignments to earn a certificate.')
    return True


def render_certificate_pdf(student_name, course_title, instructor_name, completion_date, certificate_id, platform_name):
    try:
        return _render_with_reportlab(student_name, course_title, instructor_name, completion_date, certificate_id, platform_name)
    except Exception:
        return _minimal_pdf_fallback(student_name, course_title, certificate_id)


def _render_with_reportlab(student_name, course_title, instructor_name, completion_date, certificate_id, platform_name):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    # Border
    c.setStrokeColorRGB(0.2, 0.35, 0.6)
    c.setLineWidth(4)
    c.rect(10 * mm, 10 * mm, page_w - 20 * mm, page_h - 20 * mm)
    c.setLineWidth(1)
    c.rect(13 * mm, 13 * mm, page_w - 26 * mm, page_h - 26 * mm)
    # Text
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(page_w / 2, page_h - 45 * mm, 'Certificate of Completion')
    c.setFont('Helvetica', 14)
    c.drawCentredString(page_w / 2, page_h - 60 * mm, f'{platform_name} certifies that')
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(page_w / 2, page_h - 75 * mm, student_name)
    c.setFont('Helvetica', 14)
    c.drawCentredString(page_w / 2, page_h - 88 * mm, 'has successfully completed the course')
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(page_w / 2, page_h - 102 * mm, course_title)
    c.setFont('Helvetica', 12)
    c.drawCentredString(page_w / 2, page_h - 118 * mm, f'Instructor: {instructor_name}')
    c.drawCentredString(page_w / 2, page_h - 128 * mm, f'Completed: {completion_date}    •    Certificate ID: {certificate_id}')
    c.setFont('Helvetica-Oblique', 10)
    c.drawCentredString(page_w / 2, 25 * mm, f'Verify at /certificates/verify/{certificate_id}/')
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def _minimal_pdf_fallback(student_name, course_title, certificate_id):
    """Minimal valid PDF for interpreters where reportlab's md5 call is unsupported (old Python/OpenSSL)."""
    text = f'Certificate of Completion - {student_name} - {course_title} - {certificate_id}'
    safe = ''.join(ch if 32 <= ord(ch) < 127 else '?' for ch in text)
    body = f'BT /F1 18 Tf 72 720 Td ({safe}) Tj ET'
    objects = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
        f'<< /Length {len(body)} >>\nstream\n{body}\nendstream',
        '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]
    pdf = ['%PDF-1.4']
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(sum(len(line) + 1 for line in pdf))
        pdf.append(f'{i} 0 obj')
        pdf.append(obj)
        pdf.append('endobj')
    xref_pos = sum(len(line) + 1 for line in pdf)
    pdf.append(f'xref\n0 {len(objects) + 1}\n0000000000 65535 f ')
    for off in offsets:
        pdf.append(f'{off:010d} 00000 n ')
    pdf.append(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF')
    return ('\n'.join(pdf)).encode('latin-1')


def generate_certificate(enrollment):
    """Create (or return existing) certificate for a completed enrollment."""
    from .models import Certificate

    check_eligibility(enrollment)
    existing = Certificate.objects.filter(student=enrollment.student, course=enrollment.course).first()
    if existing:
        return existing, False
    student = enrollment.student
    course = enrollment.course
    try:
        instructor_name = course.instructor.profile.display_name()
    except Exception:
        instructor_name = course.instructor.get_full_name() or course.instructor.username
    student_name = getattr(student, 'get_full_name', lambda: '')() or student.username
    try:
        student_name = student.profile.display_name()
    except Exception:
        pass
    completion_date = enrollment.completed_at.date().isoformat() if enrollment.completed_at else ''
    platform_name = getattr(settings, 'PLATFORM_NAME', 'LearnHub')
    cert = Certificate(student=student, course=course, instructor_name=instructor_name)
    cert.save()  # generates certificate_id
    pdf_bytes = render_certificate_pdf(student_name, course.title, instructor_name, completion_date, cert.certificate_id, platform_name)
    cert.pdf.save(f'certificate_{cert.certificate_id}.pdf', ContentFile(pdf_bytes), save=True)
    return cert, True
