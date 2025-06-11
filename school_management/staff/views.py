from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from .models import Teacher
from .forms import TeacherForm

class TeacherListView(ListView):
    model = Teacher
    template_name = 'staff/teacher_list.html'

class TeacherCreateView(CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'staff/teacher_form.html'
    success_url = reverse_lazy('teacher_list')

class TeacherDetailView(DetailView):
    model = Teacher
    template_name = 'staff/teacher_detail.html'