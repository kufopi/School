from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomAuthenticationForm
from django.views.generic import TemplateView
from students.models import Student
from staff.models import Teacher
from finance.models import Invoice,Payment
from events.models import Event
from django.utils import timezone



# In views.py
class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        user = form.get_user()
        if not user.is_approved and not user.is_superuser:
            messages.warning(self.request, "Your account is pending approval")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect based on user type
        user = self.request.user
        if user.user_type == 'student':
            return reverse_lazy('student_dashboard_self')
        elif user.user_type == 'teacher':
            return reverse_lazy('teacher_dashboard')
        elif user.user_type == 'parent':
            return reverse_lazy('parent_dashboard')
        return reverse_lazy('dashboard')  # Changed from 'admin_dashboard' to 'dashboard'

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Common context for all users
        context['current_term'] = SchoolTerm.objects.filter(is_current=True).first()
        
        if user.user_type in ['admin', 'staff']:
            context.update({
                'student_count': Student.objects.count(),
                'teacher_count': Teacher.objects.filter(is_active=True).count(),
                'pending_invoices': Invoice.objects.filter(is_paid=False).count(),
                'upcoming_events': Event.objects.filter(start_date__gte=timezone.now())[:5],
                'recent_payments': Payment.objects.order_by('-payment_date')[:5]
            })
        elif user.user_type == 'teacher':
            context['teacher_classes'] = user.teacher.classes_assigned.all()
        elif user.user_type == 'student':
            context['student_classes'] = user.student.classes.all()
        elif user.user_type == 'parent':
            context['children'] = user.parent.children.all()
            
        return context
    

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from core.forms import SchoolSessionForm, SchoolTermForm
from core.models import SchoolSession, SchoolTerm

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

@user_passes_test(is_admin, login_url='/login/')
def create_session(request):
    if request.method == 'POST':
        form = SchoolSessionForm(request.POST)
        if form.is_valid():
            # Ensure only one session is marked as current
            if form.cleaned_data['is_current']:
                SchoolSession.objects.filter(is_current=True).update(is_current=False)
            form.save()
            messages.success(request, 'Session created successfully!')
            return redirect('session_list')
    else:
        form = SchoolSessionForm()
    
    return render(request, 'admin/create_session.html', {'form': form})

@user_passes_test(is_admin, login_url='/login/')
def session_list(request):
    sessions = SchoolSession.objects.all().order_by('-start_date')
    return render(request, 'admin/session_list.html', {'sessions': sessions})

@user_passes_test(is_admin, login_url='/login/')
def create_term(request):
    if request.method == 'POST':
        form = SchoolTermForm(request.POST)
        if form.is_valid():
            # Ensure only one term is marked as current
            if form.cleaned_data['is_current']:
                SchoolTerm.objects.filter(is_current=True).update(is_current=False)
            form.save()
            messages.success(request, 'Term created successfully!')
            return redirect('term_list')
    else:
        form = SchoolTermForm()
    
    return render(request, 'admin/create_term.html', {'form': form})

@user_passes_test(is_admin, login_url='/login/')
def term_list(request):
    terms = SchoolTerm.objects.all().order_by('-session__start_date', 'name')
    return render(request, 'admin/term_list.html', {'terms': terms})


# # In views.py
# class AdminDashboardView(LoginRequiredMixin, TemplateView):
#     template_name = 'core/admin_dashboard.html'
#     login_url = reverse_lazy('login')
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Add admin-specific context here
#         return context