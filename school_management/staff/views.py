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


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.utils import timezone
import json

from .models import Teacher, ClassTeacher
from students.models import Student, StudentHealthRecord, BehaviorAssessment, AttendanceRecord
from academics.models import Subject, Result, ExamType, ClassSubject, TermReport
from core.models import SchoolTerm
from students.forms import StudentHealthForm, BehaviorAssessmentForm, AttendanceForm
from academics.forms import ResultForm


@login_required
def teacher_dashboard(request):
    """Main teacher dashboard view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "You are not registered as a teacher.")
        return redirect('home')
    
    # Get current term
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    # Get classes taught by this teacher
    subjects_taught = ClassSubject.objects.filter(
        teacher=teacher
    ).select_related('class_info', 'subject')
    
    # Check if teacher is a class teacher
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        academic_session__is_current=True
    ).select_related('class_assigned').first()
    
    context = {
        'teacher': teacher,
        'current_term': current_term,
        'subjects_taught': subjects_taught,
        'class_teacher_assignment': class_teacher_assignment,
    }
    
    return render(request, 'staff/teacher_dashboard.html', context)


@login_required
def enter_subject_scores(request, class_subject_id):
    """View for entering subject scores for a specific class-subject combination"""
    teacher = get_object_or_404(Teacher, user=request.user)
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id, teacher=teacher)
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    if not current_term:
        messages.error(request, "No active term found.")
        return redirect('teacher_dashboard')
    
    # Get all students in this class
    students = Student.objects.filter(
        current_class=class_subject.class_info,
        is_active=True
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    # Get available exam types
    exam_types = ExamType.objects.all()
    
    if request.method == 'POST':
        exam_type_id = request.POST.get('exam_type')
        exam_type = get_object_or_404(ExamType, id=exam_type_id)
        
        errors = []
        success_count = 0
        
        for student in students:
            score_key = f'score_{student.id}'
            score = request.POST.get(score_key)
            
            if score and score.strip():
                try:
                    score = float(score)
                    
                    # Validate score
                    if score < 0 or score > exam_type.max_score:
                        errors.append(f"{student.user.get_full_name()}: Score must be between 0 and {exam_type.max_score}")
                        continue
                    
                    # Get or create term report
                    term_report, _ = TermReport.objects.get_or_create(
                        student=student,
                        term=current_term,
                        defaults={'created_by': request.user}
                    )
                    
                    # Create or update result
                    result, created = Result.objects.update_or_create(
                        student=student,
                        term=current_term,
                        subject=class_subject.subject,
                        exam_type=exam_type,
                        defaults={
                            'score': score,
                            'recorded_by': teacher,
                            'term_report': term_report
                        }
                    )
                    success_count += 1
                    
                except ValueError:
                    errors.append(f"{student.user.get_full_name()}: Invalid score format")
        
        if errors:
            for error in errors:
                messages.warning(request, error)
        
        if success_count > 0:
            messages.success(request, f"Successfully recorded {success_count} scores for {exam_type.name}")
        
        return redirect('enter_subject_scores', class_subject_id=class_subject_id)
    
    # Get existing results for display
    selected_exam_type_id = request.GET.get('exam_type')
    students_with_scores = []
    
    # Always populate students_with_scores, regardless of exam type selection
    for student in students:
        existing_score = ''
        
        if selected_exam_type_id:
            # Try to get existing result for this student
            try:
                result = Result.objects.get(
                    student=student,
                    term=current_term,
                    subject=class_subject.subject,
                    exam_type_id=selected_exam_type_id
                )
                existing_score = result.score
            except Result.DoesNotExist:
                existing_score = ''
        
        students_with_scores.append({
            'student': student,
            'existing_score': existing_score
        })
    
    context = {
        'teacher': teacher,
        'class_subject': class_subject,
        'current_term': current_term,
        'students': students,
        'students_with_scores': students_with_scores,
        'exam_types': exam_types,
        'selected_exam_type_id': selected_exam_type_id,
    }
    
    return render(request, 'staff/enter_subject_scores.html', context)


@login_required
def class_teacher_dashboard(request):
    """Dashboard for class teachers to manage student records"""
    teacher = get_object_or_404(Teacher, user=request.user)
    
    # Check if teacher is a class teacher
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        academic_session__is_current=True
    ).select_related('class_assigned').first()
    
    if not class_teacher_assignment:
        messages.error(request, "You are not assigned as a class teacher.")
        return redirect('teacher_dashboard')
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    # Get all students in the class
    students = Student.objects.filter(
        current_class=class_teacher_assignment.class_assigned,
        is_active=True
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    context = {
        'teacher': teacher,
        'class_teacher_assignment': class_teacher_assignment,
        'current_term': current_term,
        'students': students,
    }
    
    return render(request, 'staff/class_teacher_dashboard.html', context)


@login_required
def enter_health_records(request, student_id):
    """Enter health records for a student"""
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=student_id)
    
    # Verify teacher is the class teacher
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        class_assigned=student.current_class,
        academic_session__is_current=True
    ).first()
    
    if not class_teacher_assignment:
        messages.error(request, "You are not the class teacher for this student.")
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        form = StudentHealthForm(request.POST)
        if form.is_valid():
            health_record = form.save(commit=False)
            health_record.student = student
            health_record.save()
            messages.success(request, f"Health record added for {student.user.get_full_name()}")
            return redirect('class_teacher_dashboard')
    else:
        form = StudentHealthForm()
    
    # Get recent health records
    recent_records = StudentHealthRecord.objects.filter(
        student=student
    ).order_by('-record_date')[:5]
    
    context = {
        'form': form,
        'student': student,
        'recent_records': recent_records,
    }
    
    return render(request, 'staff/enter_health_records.html', context)


@login_required
def enter_behavior_assessment(request, student_id):
    """Enter behavioral assessment for a student"""
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=student_id)
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    if not current_term:
        messages.error(request, "No active term found.")
        return redirect('class_teacher_dashboard')
    
    # Verify teacher is the class teacher
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        class_assigned=student.current_class,
        academic_session__is_current=True
    ).first()
    
    if not class_teacher_assignment:
        messages.error(request, "You are not the class teacher for this student.")
        return redirect('teacher_dashboard')
    
    # Check if assessment already exists for this term
    existing_assessment = BehaviorAssessment.objects.filter(
        student=student,
        term=current_term
    ).first()
    
    if request.method == 'POST':
        form = BehaviorAssessmentForm(request.POST, instance=existing_assessment)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.student = student
            assessment.term = current_term
            assessment.assessed_by = teacher
            assessment.save()
            
            action = "updated" if existing_assessment else "added"
            messages.success(request, f"Behavior assessment {action} for {student.user.get_full_name()}")
            return redirect('class_teacher_dashboard')
    else:
        form = BehaviorAssessmentForm(instance=existing_assessment)
    
    context = {
        'form': form,
        'student': student,
        'current_term': current_term,
        'existing_assessment': existing_assessment,
    }
    
    return render(request, 'staff/enter_behavior_assessment.html', context)


@login_required
def enter_attendance(request, student_id):
    """Enter attendance records for a student"""
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=student_id)
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    if not current_term:
        messages.error(request, "No active term found.")
        return redirect('class_teacher_dashboard')
    
    # Verify teacher is the class teacher
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        class_assigned=student.current_class,
        academic_session__is_current=True
    ).first()
    
    if not class_teacher_assignment:
        messages.error(request, "You are not the class teacher for this student.")
        return redirect('teacher_dashboard')
    
    # Get or create attendance record for current term
    attendance, created = AttendanceRecord.objects.get_or_create(
        student=student,
        term=current_term
    )
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Attendance updated for {student.user.get_full_name()}")
            return redirect('class_teacher_dashboard')
    else:
        form = AttendanceForm(instance=attendance)
    
    context = {
        'form': form,
        'student': student,
        'current_term': current_term,
        'attendance': attendance,
    }
    
    return render(request, 'staff/enter_attendance.html', context)


@login_required
def bulk_attendance_entry(request):
    """Bulk entry for attendance records for all students in class"""
    teacher = get_object_or_404(Teacher, user=request.user)
    
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        academic_session__is_current=True
    ).select_related('class_assigned').first()
    
    if not class_teacher_assignment:
        messages.error(request, "You are not assigned as a class teacher.")
        return redirect('teacher_dashboard')
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    if not current_term:
        messages.error(request, "No active term found.")
        return redirect('class_teacher_dashboard')
    
    students = Student.objects.filter(
        current_class=class_teacher_assignment.class_assigned,
        is_active=True
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    if request.method == 'POST':
        success_count = 0
        
        for student in students:
            present_key = f'days_present_{student.id}'
            absent_key = f'days_absent_{student.id}'
            
            days_present = request.POST.get(present_key)
            days_absent = request.POST.get(absent_key)
            
            if days_present is not None or days_absent is not None:
                attendance, created = AttendanceRecord.objects.get_or_create(
                    student=student,
                    term=current_term
                )
                
                if days_present:
                    attendance.days_present = int(days_present)
                if days_absent:
                    attendance.days_absent = int(days_absent)
                
                attendance.save()
                success_count += 1
        
        messages.success(request, f"Attendance updated for {success_count} students")
        return redirect('class_teacher_dashboard')
    
    # Get existing attendance records
    attendance_records = AttendanceRecord.objects.filter(
        student__in=students,
        term=current_term
    ).select_related('student')
    
    attendance_dict = {}
    for record in attendance_records:
        attendance_dict[record.student.id] = {
            'days_present': record.days_present,
            'days_absent': record.days_absent,
            'total_days': record.days_present + record.days_absent,
            'rate': record.attendance_rate
        }
    
    context = {
        'teacher': teacher,
        'class_teacher_assignment': class_teacher_assignment,
        'current_term': current_term,
        'students': students,
        'attendance_dict': json.dumps(attendance_dict),
    }
    
    return render(request, 'staff/bulk_attendance_entry.html', context)

from academics.models import TermReport, ReportComment, PredefinedComment
from academics.forms import ReportCommentForm

@login_required
def enter_term_comment(request, student_id):
    """Enter term performance comment for a student"""
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=student_id)
    
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    if not current_term:
        messages.error(request, "No active term found.")
        return redirect('class_teacher_dashboard')
    
    # Verify teacher is the class teacher
    class_teacher_assignment = ClassTeacher.objects.filter(
        teacher=teacher,
        class_assigned=student.current_class,
        academic_session__is_current=True
    ).first()
    
    if not class_teacher_assignment:
        messages.error(request, "You are not the class teacher for this student.")
        return redirect('teacher_dashboard')
    
    # Get or create term report
    term_report, created = TermReport.objects.get_or_create(
        student=student,
        term=current_term,
        defaults={'created_by': request.user}
    )
    
    # Check if comment already exists
    existing_comment = ReportComment.objects.filter(
        report=term_report,
        comment_type='teacher'
    ).first()
    
    # Get predefined comments
    predefined_comments = PredefinedComment.objects.filter(
        comment_type='teacher'
    )
    
    if request.method == 'POST':
        form = ReportCommentForm(request.POST, instance=existing_comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.report = term_report
            comment.added_by = request.user
            comment.comment_type = 'teacher'  # Force teacher comment type
            comment.save()
            
            action = "updated" if existing_comment else "added"
            messages.success(request, f"Term comment {action} for {student.user.get_full_name()}")
            return redirect('class_teacher_dashboard')
    else:
        form = ReportCommentForm(instance=existing_comment)
    
    context = {
        'form': form,
        'student': student,
        'current_term': current_term,
        'existing_comment': existing_comment,
        'predefined_comments': predefined_comments,
        'term_report': term_report,
    }
    
    return render(request, 'staff/enter_term_comment.html', context)