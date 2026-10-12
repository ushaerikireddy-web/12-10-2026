from django.urls import path

from .views import (
    CustomLoginView,
    CustomLogoutView,
    InstructorRegisterView,
    ProfileDetailView,
    ProfileUpdateView,
    StudentRegisterView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', StudentRegisterView.as_view(), name='register'),
    path('register/instructor/', InstructorRegisterView.as_view(), name='register-instructor'),
    path('profile/', ProfileDetailView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile-edit'),
]
