from django.urls import path
from .views import TeacherListView, TeacherCreateView, TeacherDetailView
from . import views

urlpatterns = [
    path('teacher/', TeacherListView.as_view(), name='teacher_list'),
    path('add/', TeacherCreateView.as_view(), name='teacher_create'),
    path('<int:pk>/', TeacherDetailView.as_view(), name='teacher_detail'),

    # Teacher Dashboard URLs
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/scores/<int:class_subject_id>/', views.enter_subject_scores, name='enter_subject_scores'),
    
    # Class Teacher URLs
    path('dashboard/class-teacher/', views.class_teacher_dashboard, name='class_teacher_dashboard'),
    path('dashboard/health/<int:student_id>/', views.enter_health_records, name='enter_health_records'),
    path('dashboard/behavior/<int:student_id>/', views.enter_behavior_assessment, name='enter_behavior_assessment'),
    path('dashboard/attendance/<int:student_id>/', views.enter_attendance, name='enter_attendance'),
    path('dashboard/attendance/bulk/', views.bulk_attendance_entry, name='bulk_attendance_entry'),

    path('dashboard/comment/<int:student_id>/', views.enter_term_comment, name='enter_term_comment'),
]