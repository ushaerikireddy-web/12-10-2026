from django.urls import path

from .views import QuizTakeView, TestListView

app_name = 'quizzes'

urlpatterns = [
    path('tests/', TestListView.as_view(), name='test-list'),
    path('quiz/<slug:slug>/', QuizTakeView.as_view(), name='quiz-take'),
]
