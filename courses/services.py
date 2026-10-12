"""Progress calculation: 70% lessons + 30% published assignments."""
from django.utils import timezone


def recalculate_enrollment_progress(enrollment):
    """Recompute enrollment.progress and completed flag. Returns enrollment."""
    from .models import Lesson, LessonProgress
    from assignments.models import Submission

    course = enrollment.course
    lessons = Lesson.objects.filter(module__course=course)
    total_lessons = lessons.count()
    done_lessons = LessonProgress.objects.filter(
        enrollment=enrollment, lesson__in=lessons, completed=True
    ).count()

    published_assignments = course.assignments.filter(is_published=True)
    total_assignments = published_assignments.count()
    submitted_assignments = Submission.objects.filter(
        assignment__in=published_assignments, student=enrollment.student
    ).count()

    lesson_pct = (done_lessons / total_lessons * 70.0) if total_lessons else 0.0
    # If a course has no lessons, lessons contribute nothing; if no assignments, lessons scale to 100.
    if total_lessons and not total_assignments:
        lesson_pct = done_lessons / total_lessons * 100.0
        assignment_pct = 0.0
    elif not total_lessons and total_assignments:
        lesson_pct = 0.0
        assignment_pct = submitted_assignments / total_assignments * 100.0
    elif not total_lessons and not total_assignments:
        lesson_pct, assignment_pct = 0.0, 0.0
    else:
        assignment_pct = submitted_assignments / total_assignments * 30.0

    progress = round(min(lesson_pct + assignment_pct, 100.0), 2)
    enrollment.progress = progress

    lessons_done = (total_lessons == 0) or (done_lessons >= total_lessons)
    assignments_done = (total_assignments == 0) or (submitted_assignments >= total_assignments)
    # A course with no content cannot auto-complete.
    if total_lessons == 0 and total_assignments == 0:
        enrollment.completed = False
        enrollment.completed_at = None
    elif lessons_done and assignments_done:
        if not enrollment.completed:
            enrollment.completed = True
            enrollment.completed_at = timezone.now()
    else:
        enrollment.completed = False
        enrollment.completed_at = None
    enrollment.save(update_fields=['progress', 'completed', 'completed_at'])
    return enrollment


def mark_lesson_complete(enrollment, lesson):
    from django.utils import timezone as tz

    from .models import LessonProgress
    record, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    if not record.completed:
        record.completed = True
        record.completed_at = tz.now()
        record.save(update_fields=['completed', 'completed_at'])
    return recalculate_enrollment_progress(enrollment)
