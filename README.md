# Online Student Learning Platform — Backend (Django + MySQL)

Complete backend for an online learning platform. Bootstrap-compatible server-rendered templates + DRF read API for JS frontends.

## Apps
| App | Responsibility |
|---|---|
| `accounts` | Custom `User` (STUDENT/INSTRUCTOR/ADMIN), `Profile`, registration/login/logout, role mixins |
| `courses` | `Category`, `Course`, `Module`, `Lesson`, `Enrollment`, `LessonProgress`, search/filter/pagination, progress service |
| `assignments` | `Assignment`, `Submission`, late policy, grading |
| `certificates` | Eligibility-gated PDF certificates (reportlab), verification |
| `pages` | `AboutUs` singleton content, `ContactMessage` with honeypot + IP rate limiting |
| `dashboard` | Student / Instructor / Admin dashboards |
| `config.api_urls` | DRF read-only `/api/courses/`, `/api/categories/` |

## Quick start (SQLite, Windows PowerShell)

```powershell
cd "opencode project_3"
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations accounts courses assignments certificates pages
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/sample_data.json
python manage.py runserver
```

Open: http://127.0.0.1:8000/ (courses), `/dashboard/`, `/admin/`, `/api/courses/`.

## MySQL setup

```sql
CREATE DATABASE learning_platform CHARACTER SET utf8mb4;
CREATE USER 'lp_user'@'%' IDENTIFIED BY 'strong-password';
GRANT ALL ON learning_platform.* TO 'lp_user'@'%';
```

`.env`:
```
DB_ENGINE=mysql
DB_NAME=learning_platform
DB_USER=lp_user
DB_PASSWORD=strong-password
DB_HOST=127.0.0.1
DB_PORT=3306
```
Then `python manage.py migrate`.

## Key workflows
- **Register** `/accounts/register/` → auto-login as STUDENT. Instructor: `/accounts/register/instructor/` (gate to admins in production).
- **Instructor**: create course → add modules → add lessons (URL or file) → publish → create assignments.
- **Student**: browse/search courses → Enroll (duplicate-safe via `unique_together` + `get_or_create`) → watch lessons → Mark Complete → submit assignments → progress auto-recalculates (70% lessons / 30% assignments; 100% lessons when no assignments).
- **Certificate**: course page "Get Certificate" (POST `/certificates/generate/<course_id>/`) only when `completed`; one cert per student+course; download PDF; verify at `/certificates/verify/<ID>/`.
- **Contact**: `/pages/contact/` (honeypot + 5/hour/IP). **About**: `/pages/about/` editable in admin.

## Tests
```powershell
python manage.py test
```

## Production security checklist
- [ ] `DJANGO_DEBUG=False`, strong `DJANGO_SECRET_KEY`, real `ALLOWED_HOSTS`
- [ ] Gate instructor registration to admins; enforce HTTPS (`SECURE_SSL_REDIRECT`, secure cookies — auto-enabled when `DEBUG=False`)
- [ ] Use SMTP email backend; configure `DEFAULT_FROM_EMAIL`
- [ ] Serve media via S3/CDN with signed URLs for paid content; restrict `MEDIA_ROOT` access
- [ ] Set DB credentials via secrets manager; least-privilege MySQL user
- [ ] `python manage.py check --deploy`, enable logging/monitoring, backups
- [ ] `collectstatic` behind WhiteNoise or CDN
