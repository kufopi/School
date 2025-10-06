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


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Max, Min
from decimal import Decimal, InvalidOperation
import math

def calculate_grade(score):
    """Calculate letter grade based on score"""
    try:
        score = float(score)
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B'
        elif score >= 60: return 'C'
        elif score >= 50: return 'D'
        else: return 'F'
    except (ValueError, TypeError):
        return 'F'

@login_required
def student_dashboard(request, student_id=None):
    # If no student_id provided, use logged-in student (for student users)
    if student_id is None:
        if not hasattr(request.user, 'student'):
            raise PermissionDenied
        student = request.user.student
    else:
        student = get_object_or_404(Student, pk=student_id)
        
        # Simplified permission checking
        if not request.user.is_superuser:
            if hasattr(request.user, 'user_type'):
                if request.user.user_type == 'student' and request.user.student != student:
                    raise PermissionDenied
            else:
                raise PermissionDenied
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    def safe_decimal_value(value):
        """Safely convert any value to float"""
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    return 0.0
                return float(value)
            if isinstance(value, Decimal):
                if value.is_nan() or value.is_infinite():
                    return 0.0
                return float(value)
            return float(value)
        except (ValueError, TypeError, InvalidOperation, OverflowError):
            return 0.0
    
    # Academic Data - with safe decimal handling
    academic_data = []
    try:
        # Get all results
        all_results = Result.objects.filter(student=student).select_related('exam_type', 'term')
        
        # Group by term and subject
        term_subject_data = {}
        for result in all_results:
            term_id = result.term.id
            subject_id = result.subject.id
            
            if term_id not in term_subject_data:
                term_subject_data[term_id] = {
                    'term__name': result.term.name,
                    'term__start_date': result.term.start_date,
                    'subjects': {}
                }
            
            if subject_id not in term_subject_data[term_id]['subjects']:
                term_subject_data[term_id]['subjects'][subject_id] = {
                    'weighted_total': 0.0,
                    'total_weight': 0.0
                }
            
            # Add weighted contribution
            weighted_contribution = (float(result.score) / float(result.exam_type.max_score)) * float(result.exam_type.weight)
            term_subject_data[term_id]['subjects'][subject_id]['weighted_total'] += weighted_contribution
            term_subject_data[term_id]['subjects'][subject_id]['total_weight'] += result.exam_type.weight
        
        # Calculate term averages (average of subject final scores)
        for term_id, data in term_subject_data.items():
            subject_scores = []
            for subject_id, subject_data in data['subjects'].items():
                if subject_data['total_weight'] > 0:
                    final_score = subject_data['weighted_total']  # Already out of 100
                    subject_scores.append(final_score)
            
            term_avg = sum(subject_scores) / len(subject_scores) if subject_scores else 0
            
            academic_data.append({
                'term__name': data['term__name'],
                'term__start_date': data['term__start_date'],
                'term_avg': term_avg
            })
            
    except Exception as e:
        academic_data = []
    
    # Class statistics calculation
    class_stats = {}
    try:
        if current_term and student.current_class:
            # Get number of students in the class
            class_student_count = Student.objects.filter(
                current_class=student.current_class,
                is_active=True
            ).count()
            
            # Get class average for current term using simplified approach
            class_results = Result.objects.filter(
                term=current_term,
                student__current_class=student.current_class,
                student__is_active=True
            )
            
            if class_results.exists():
                # Calculate simple average of all scores
                class_avg = class_results.aggregate(avg_score=Avg('score'))['avg_score'] or 0
            else:
                class_avg = 0
                
            class_stats = {
                'student_count': class_student_count,
                'class_average': safe_decimal_value(class_avg)
            }
        else:
            class_stats = {
                'student_count': 0,
                'class_average': 0
            }
    except Exception as e:
        class_stats = {
            'student_count': 0,
            'class_average': 0
        }
    
    # Health Data
    try:
        health_records = StudentHealthRecord.objects.filter(
            student=student
        ).order_by('-record_date')[:6]
    except Exception:
        health_records = []
    
    # Behavior Data
    try:
        behavior_assessments = BehaviorAssessment.objects.filter(
            student=student
        ).select_related('term').order_by('-term__start_date')
    except Exception:
        behavior_assessments = []
    
    # Attendance Data
    try:
        attendance_records = AttendanceRecord.objects.filter(
            student=student
        ).select_related('term').order_by('-term__start_date')
    except Exception:
        attendance_records = []
    
    # Current Term Stats - WEIGHTED SCORES
    safe_subjects = []
    try:
        if current_term:
            # Get all results for current term
            current_results = Result.objects.filter(
                student=student,
                term=current_term
            ).select_related('exam_type', 'subject')
            
            # Group results by subject and calculate weighted scores
            subject_data = {}
            for result in current_results:
                subject_id = result.subject.id
                if subject_id not in subject_data:
                    subject_data[subject_id] = {
                        'subject__name': result.subject.name,
                        'results': [],
                        'weighted_total': 0.0,
                        'total_weight': 0.0,
                        'raw_scores': []
                    }
                
                # Calculate weighted contribution for this result
                weighted_contribution = (float(result.score) / float(result.exam_type.max_score)) * float(result.exam_type.weight)
                subject_data[subject_id]['weighted_total'] += weighted_contribution
                subject_data[subject_id]['total_weight'] += result.exam_type.weight
                subject_data[subject_id]['results'].append(result)
                subject_data[subject_id]['raw_scores'].append(float(result.score))
            
            # Calculate final weighted scores for each subject
            for subject_id, data in subject_data.items():
                final_score = 0.0
                if data['total_weight'] > 0:
                    final_score = data['weighted_total']  # This is already out of 100
                
                safe_subjects.append({
                    'subject__name': data['subject__name'],
                    'subject__id': subject_id,
                    'final_score': safe_decimal_value(final_score),
                    'avg_score': safe_decimal_value(sum(data['raw_scores']) / len(data['raw_scores'])) if data['raw_scores'] else 0,
                    'highest_score': safe_decimal_value(max(data['raw_scores'])) if data['raw_scores'] else 0,
                    'lowest_score': safe_decimal_value(min(data['raw_scores'])) if data['raw_scores'] else 0,
                    'grade': calculate_grade(final_score)
                })
    except Exception as e:
        safe_subjects = []
    
    # Get current behavior and attendance safely
    current_behavior = None
    current_attendance = None
    
    if current_term:
        try:
            current_behavior = behavior_assessments.filter(term=current_term).first()
        except Exception:
            pass
        
        try:
            current_attendance = attendance_records.filter(term=current_term).first()
        except Exception:
            pass
    
    current_stats = {
        'behavior': current_behavior,
        'attendance': current_attendance,
        'subjects': safe_subjects
    }
    
    # Simplified can_edit permission
    can_edit = request.user.is_superuser
    if hasattr(request.user, 'user_type'):
        can_edit = can_edit or request.user.user_type in ['teacher', 'admin']
    
    context = {
        'student': student,
        'current_term': current_term,
        'academic_data': academic_data,
        'health_records': health_records,
        'behavior_assessments': behavior_assessments,
        'attendance_records': attendance_records,
        'current_stats': current_stats,
        'class_stats': class_stats,
        'skill_labels': ['Participation', 'Responsibility', 'Creativity', 'Cooperation'],
        'can_edit': can_edit
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


from academics.models import TermReport
from django.http import HttpResponse
from academics.utils import generate_term_report_pdf

@login_required
def student_term_report(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    if not current_term:
        return HttpResponse("No current term found", status=404)
    
    # Check permissions (same as dashboard)
    if not request.user.is_superuser:
        if hasattr(request.user, 'user_type'):
            if request.user.user_type == 'student' and request.user.student != student:
                raise PermissionDenied
        else:
            raise PermissionDenied
    
    # Get or create term report
    term_report, created = TermReport.objects.get_or_create(
        student=student,
        term=current_term,
        defaults={'created_by': request.user}
    )
    
    # Check if PDF download is requested
    if request.GET.get('download') == 'pdf':
        pdf_buffer = generate_term_report_pdf(term_report)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        filename = f"term_report_{student.student_id}_{current_term.name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    # Get subject results with weighted scores
    subject_results = []
    try:
        results = Result.objects.filter(
            student=student,
            term=current_term
        ).select_related('exam_type', 'subject')
        
        # Group by subject
        subject_data = {}
        for result in results:
            subject_id = result.subject.id
            if subject_id not in subject_data:
                subject_data[subject_id] = {
                    'subject': result.subject,
                    'results': [],
                    'weighted_total': 0.0,
                    'total_weight': 0.0,
                    'exam_breakdown': {}
                }
            
            # Calculate weighted contribution
            weighted_contribution = (float(result.score) / float(result.exam_type.max_score)) * float(result.exam_type.weight)
            subject_data[subject_id]['weighted_total'] += weighted_contribution
            subject_data[subject_id]['total_weight'] += result.exam_type.weight
            subject_data[subject_id]['results'].append(result)
            
            # Store exam breakdown
            exam_type_name = result.exam_type.name
            subject_data[subject_id]['exam_breakdown'][exam_type_name] = {
                'score': float(result.score),
                'max_score': result.exam_type.max_score,
                'weight': result.exam_type.weight,
                'weighted_contribution': weighted_contribution
            }
        
        # Prepare final subject results
        for subject_id, data in subject_data.items():
            final_score = data['weighted_total'] if data['total_weight'] > 0 else 0
            subject_results.append({
                'subject': data['subject'],
                'final_score': final_score,
                'grade': calculate_grade(final_score),
                'exam_breakdown': data['exam_breakdown'],
                'has_all_results': data['total_weight'] >= 100  # Check if all exam types are present
            })
            
    except Exception as e:
        subject_results = []
    
    context = {
        'student': student,
        'current_term': current_term,
        'term_report': term_report,
        'subject_results': subject_results,
        'can_edit': request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type in ['teacher', 'admin'])
    }
    
    return render(request, 'students/term_report.html', context)