from django.urls import path
from .views import CustomLoginView, CustomLogoutView, DashboardView
from core.views import (
    create_session, session_list,
    create_term, term_list
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('admin/sessions/', session_list, name='session_list'),
    path('admin/sessions/create/', create_session, name='create_session'),
    path('admin/terms/', term_list, name='term_list'),
    path('admin/terms/create/', create_term, name='create_term'),
    # path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
]