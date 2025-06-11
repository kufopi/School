from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import Student, StudentMedicalHistory,AttendanceRecord,BehaviorAssessment,StudentHealthRecord
from .forms import StudentForm, MedicalHistoryForm
from django.shortcuts import get_object_or_404,render
from core.models import SchoolTerm
from academics.models import Result
from django.db.models import Avg, Max, Min

class StudentListView(ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

class StudentDetailView(DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medical_history'] = self.object.studentmedicalhistory_set.all()
        return context

class MedicalHistoryCreateView(CreateView):
    model = StudentMedicalHistory
    form_class = MedicalHistoryForm
    template_name = 'students/medical_history_form.html'
    
    def form_valid(self, form):
        form.instance.student = Student.objects.get(pk=self.kwargs['pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('student_detail', kwargs={'pk': self.kwargs['pk']})
    

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

@login_required
def student_dashboard(request, student_id=None):
    # If no student_id provided, use logged-in student (for student users)
    if student_id is None:
        if not hasattr(request.user, 'student'):
            raise PermissionDenied
        student = request.user.student
    else:
        student = get_object_or_404(Student, pk=student_id)
        # Verify permission (admin/teacher/parent of this student)
        if not request.user.is_superuser:
            if request.user.user_type == 'teacher':
                if not student.current_class.teachers.filter(user=request.user).exists():
                    raise PermissionDenied
            elif request.user.user_type == 'parent':
                if not student.parents.filter(user=request.user).exists():
                    raise PermissionDenied
            elif request.user.user_type == 'student' and request.user.student != student:
                raise PermissionDenied
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    # Academic Data
    academic_data = Result.objects.filter(
        student=student
    ).values('term__name', 'term__start_date').annotate(
        term_avg=Avg('score')
    ).order_by('term__start_date')
    
    # Health Data
    health_records = StudentHealthRecord.objects.filter(
        student=student
    ).order_by('-record_date')[:6]
    
    # Behavior Data
    behavior_assessments = BehaviorAssessment.objects.filter(
        student=student
    ).select_related('term').order_by('-term__start_date')
    
    # Attendance Data
    attendance_records = AttendanceRecord.objects.filter(
        student=student
    ).select_related('term').order_by('-term__start_date')
    
    # Current Term Stats
    current_stats = {
        'behavior': behavior_assessments.filter(term=current_term).first(),
        'attendance': attendance_records.filter(term=current_term).first(),
        'subjects': Result.objects.filter(
            student=student,
            term=current_term
        ).values('subject__name').annotate(
            avg_score=Avg('score'),
            highest_score=Max('score'),
            lowest_score=Min('score')
        )
    }
    
    context = {
        'student': student,
        'current_term': current_term,
        'academic_data': academic_data,
        'health_records': health_records,
        'behavior_assessments': behavior_assessments,
        'attendance_records': attendance_records,
        'current_stats': current_stats,
        'skill_labels': ['Participation', 'Responsibility', 'Creativity', 'Cooperation'],
        'can_edit': request.user.is_superuser or 
                   request.user.user_type == 'teacher' or
                   (hasattr(request.user, 'parent') and student in request.user.parent.students.all())
    }
    return render(request, 'students/student_dashboard.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Student, StudentHealthRecord, BehaviorAssessment, AttendanceRecord
from .forms import (
    StudentHealthForm, 
    BehaviorAssessmentForm,
    ResultForm,
    AttendanceForm
)

@login_required
def edit_student_health(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    health_record = StudentHealthRecord.objects.filter(student=student).first()
    
    if request.method == 'POST':
        form = StudentHealthForm(request.POST, instance=health_record)
        if form.is_valid():
            record = form.save(commit=False)
            record.student = student
            record.save()
            return redirect('student_dashboard', student_id=student_id)
    else:
        form = StudentHealthForm(instance=health_record)
    
    return render(request, 'students/edit_health.html', {
        'form': form,
        'student': student
    })

@login_required
def add_behavior_assessment(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    if request.method == 'POST':
        form = BehaviorAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.student = student
            assessment.term = current_term
            assessment.assessed_by = request.user
            assessment.save()
            return redirect('student_dashboard', student_id=student_id)
    else:
        form = BehaviorAssessmentForm()
    
    return render(request, 'students/edit_behavior.html', {
        'form': form,
        'student': student
    })

@login_required
def edit_behavior_assessment(request, assessment_id):
    assessment = get_object_or_404(BehaviorAssessment, pk=assessment_id)
    
    if request.method == 'POST':
        form = BehaviorAssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            return redirect('student_dashboard', student_id=assessment.student.id)
    else:
        form = BehaviorAssessmentForm(instance=assessment)
    
    return render(request, 'students/edit_behavior.html', {
        'form': form,
        'student': assessment.student
    })

@login_required
def add_student_result(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    if request.method == 'POST':
        form = ResultForm(request.POST)
        if form.is_valid():
            result = form.save(commit=False)
            result.student = student
            result.term = current_term
            result.save()
            return redirect('student_dashboard', student_id=student_id)
    else:
        form = ResultForm()
    
    return render(request, 'students/edit_result.html', {
        'form': form,
        'student': student
    })

@login_required
def edit_student_result(request, student_id, subject):
    student = get_object_or_404(Student, pk=student_id)
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    result = get_object_or_404(
        Result, 
        student=student, 
        term=current_term,
        subject__name=subject
    )
    
    if request.method == 'POST':
        form = ResultForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            return redirect('student_dashboard', student_id=student_id)
    else:
        form = ResultForm(instance=result)
    
    return render(request, 'students/edit_result.html', {
        'form': form,
        'student': student,
        'subject': subject
    })

@login_required
def update_attendance(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    attendance, created = AttendanceRecord.objects.get_or_create(
        student=student,
        term=current_term,
        defaults={'days_present': 0, 'days_absent': 0}
    )
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('student_dashboard', student_id=student_id)
    else:
        form = AttendanceForm(instance=attendance)
    
    return render(request, 'students/edit_attendance.html', {
        'form': form,
        'student': student
    })