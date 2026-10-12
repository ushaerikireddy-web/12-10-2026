from django.urls import path

from .views import AdminDashboardView, DashboardHomeView, InstructorDashboardView, StudentDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),
    path('student/', StudentDashboardView.as_view(), name='student'),
    path('instructor/', InstructorDashboardView.as_view(), name='instructor'),
    path('admin/', AdminDashboardView.as_view(), name='admin'),
]
