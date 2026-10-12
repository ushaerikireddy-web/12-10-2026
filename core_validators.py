"""Shared file validators used across apps."""
import os

from django.core.exceptions import ValidationError

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.mkv'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.zip', '.ppt', '.pptx', '.xls', '.xlsx', '.csv', '.jpg', '.jpeg', '.png'}


def validate_image_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValidationError('Unsupported image format. Allowed: jpg, jpeg, png, webp, gif.')
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Image too large (max 5 MB).')


def validate_video_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in VIDEO_EXTENSIONS:
        raise ValidationError('Unsupported video format. Allowed: mp4, webm, mov, mkv.')
    if value.size > 500 * 1024 * 1024:
        raise ValidationError('Video too large (max 500 MB).')


def validate_document_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in DOCUMENT_EXTENSIONS:
        raise ValidationError('Unsupported file type for submission/attachment.')
    if value.size > 20 * 1024 * 1024:
        raise ValidationError('File too large (max 20 MB).')
