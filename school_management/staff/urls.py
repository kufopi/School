from django.urls import path
from .views import TeacherListView, TeacherCreateView, TeacherDetailView

urlpatterns = [
    path('teacher/', TeacherListView.as_view(), name='teacher_list'),
    path('add/', TeacherCreateView.as_view(), name='teacher_create'),
    path('<int:pk>/', TeacherDetailView.as_view(), name='teacher_detail'),
]