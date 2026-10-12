"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = 'Learning Platform Admin'
admin.site.site_title = 'Learning Platform'
admin.site.index_title = 'Administration'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # password reset/change
    path('courses/', include('courses.urls')),
    path('assignments/', include('assignments.urls')),
    path('certificates/', include('certificates.urls')),
    path('pages/', include('pages.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('config.api_urls')),
    path('', RedirectView.as_view(pattern_name='courses:course-list', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
