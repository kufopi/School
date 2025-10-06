from django.urls import path
from .views import StudentListView, StudentCreateView, StudentDetailView, MedicalHistoryCreateView, student_dashboard
from .views import (
    student_dashboard,
    edit_student_health,
    add_behavior_assessment,
    edit_behavior_assessment,
    add_student_result,
    edit_student_result,
    update_attendance,student_term_report,
)

urlpatterns = [
    path('sdb', StudentListView.as_view(), name='student_list'),
    path('add/', StudentCreateView.as_view(), name='student_create'),
    path('<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/medical-history/add/', MedicalHistoryCreateView.as_view(), name='medical_history_create'),
    # For students accessing their own dashboard
    path('dashboard/', student_dashboard, name='student_dashboard_self'),
    
    # For admin/teachers/parents accessing specific student dashboards
    path('dashboard/<int:student_id>/', student_dashboard, name='student_dashboard'),
    # Health Records URLs
    path('<int:student_id>/health/edit/', edit_student_health, name='edit_student_health'),

    # Behavior Assessment URLs
    path('<int:student_id>/behavior/add/', add_behavior_assessment, name='add_behavior_assessment'),
    path('behavior/<int:assessment_id>/edit/', edit_behavior_assessment, name='edit_behavior_assessment'),

    # Academic Results URLs
    path('<int:student_id>/result/add/', add_student_result, name='add_student_result'),
    path('<int:student_id>/result/<str:subject>/edit/', edit_student_result, name='edit_student_result'),

    # Attendance URLs
    path('<int:student_id>/attendance/update/', update_attendance, name='update_attendance'),
    path('<int:student_id>/term-report/', student_term_report, name='student_term_report'),
]