from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Image
from reportlab.lib.units import inch
from django.conf import settings
from django.db.models import Avg,F
from django.db import models
from django.utils import timezone
import os

def generate_term_report_pdf(report):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Set up fonts and colors
    pdf.setTitle(f"Term Report - {report.student.user.get_full_name()}")
    
    # School Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(300, 770, "PRIMARY SCHOOL NAME")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(300, 750, "TERM REPORT CARD")
    
    # Student Information Section
    student = report.student
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 720, "STUDENT INFORMATION:")
    
    # Student Photo
    photo_path = os.path.join(settings.MEDIA_ROOT, str(student.photo)) if student.photo else None
    if photo_path and os.path.exists(photo_path):
        try:
            pdf.drawImage(photo_path, 450, 680, width=1.5*inch, height=1.5*inch)
        except:
            pass  # Skip if image can't be loaded
    
    # Student Details
    info_data = [
        ["Name:", student.user.get_full_name()],
        ["Student ID:", student.student_id],
        ["Class:", str(student.current_class)],
        ["Term:", f"{report.term.name} {report.term.session.name}"],
        ["Term Dates:", f"{report.term.start_date.strftime('%b %d, %Y')} to {report.term.end_date.strftime('%b %d, %Y')}"],
    ]
    
    pdf.setFont("Helvetica", 10)
    for i, (label, value) in enumerate(info_data):
        pdf.drawString(50, 700 - (i * 20), label)
        pdf.drawString(150, 700 - (i * 20), value)
    
    # Get all results for this student and term
    results = report.result_set.all().select_related('subject')
    class_teacher = report.student.current_class.classteacher_set.filter(
        academic_session=report.term.session
    ).first()
    
    # Calculate class averages for each subject
    from academics.models import Result,TermReport
    class_avg_data = Result.objects.filter(
        term=report.term,
        student__current_class=report.student.current_class
    ).values('subject__id', 'subject__name').annotate(
        class_avg=Avg(
            (models.F('score') / models.F('exam_type__max_score')) * models.F('exam_type__weight') * 100 / models.F('exam_type__weight'),
            output_field=models.FloatField()
        )
    ).order_by('subject__name')
    
    # Prepare results table data
    data = [["Subject", "CA (40)", "Exam (60)", "Total (100)", "Grade", "Remark", "Class Avg", "Difference"]]
    subject_results = report.get_subject_results()
    student_avg = 0
    result_count = 0
    
    for result in subject_results:
        ca_score = next((r.score for r in result['results'] if r.exam_type.name.lower() == 'ca'), None)
        exam_score = next((r.score for r in result['results'] if r.exam_type.name.lower() == 'exam'), None)
        total_score = result['total_score']
        subject_avg = next(
            (item['class_avg'] for item in class_avg_data if item['subject__id'] == result['subject'].id), 0
        )
        difference = total_score - subject_avg if subject_avg else 0
        
        data.append([
            result['subject'].name,
            f"{ca_score:.1f}/40" if ca_score is not None else "-",
            f"{exam_score:.1f}/60" if exam_score is not None else "-",
            f"{total_score:.1f}/100",
            result['grade'],
            get_remark(total_score),
            f"{subject_avg:.1f}/100" if subject_avg else "-",
            f"{difference:+.1f}"
        ])
        student_avg += total_score
        result_count += 1
    
    if result_count > 0:
        student_avg = student_avg / result_count
        data.append([
            "OVERALL",
            "-",
            "-",
            f"{student_avg:.1f}/100",
            TermReport.calculate_subject_grade(None, student_avg),
            get_remark(student_avg),
            "",
            ""
        ])
    
    # Create and style results table
    table = Table(data, colWidths=[120, 60, 60, 60, 50, 80, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (6, 1), (6, -1), colors.HexColor("#555555")),
        ('TEXTCOLOR', (7, 1), (7, -1), lambda r, c: 
            colors.red if float(data[r][7]) < 0 else colors.green),
    ]))
    
    # Draw results table
    table.wrapOn(pdf, 500, 300)
    table.drawOn(pdf, 50, 400)
    
    # Overall class average comparison
    if results.exists():
        overall_class_avg = Result.objects.filter(
            term=report.term,
            student__current_class=student.current_class
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, 370, "Performance Summary:")
        
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 350, f"Your Average: {student_avg:.1f}%")
        pdf.drawString(50, 330, f"Class Average: {overall_class_avg:.1f}%")
        
        difference = student_avg - overall_class_avg
        pdf.drawString(50, 310, f"Difference: {difference:+.1f}%")
        
        # Visual indicator
        pdf.setFont("Helvetica-Bold", 10)
        if difference > 0:
            pdf.setFillColor(colors.green)
            pdf.drawString(200, 310, "↑ Above Class Average")
        elif difference < 0:
            pdf.setFillColor(colors.red)
            pdf.drawString(200, 310, "↓ Below Class Average")
        else:
            pdf.setFillColor(colors.blue)
            pdf.drawString(200, 310, "= At Class Average")
        
        pdf.setFillColor(colors.black)  # Reset color
    
    # Comments Section
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, 270, "TEACHER'S COMMENT:")
    
    teacher_comment = report.reportcomment_set.filter(comment_type='teacher').first()
    if teacher_comment:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(50, 250, teacher_comment.comment)
        pdf.drawString(400, 250, f"Date: {teacher_comment.date_added.strftime('%d-%b-%Y')}")
        if class_teacher:
            pdf.drawString(400, 235, f"Teacher: {class_teacher.teacher.user.get_full_name()}")
    
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, 200, "PRINCIPAL'S COMMENT:")
    
    principal_comment = report.reportcomment_set.filter(comment_type='principal').first()
    if principal_comment:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(50, 180, principal_comment.comment)
        pdf.drawString(400, 180, f"Date: {principal_comment.date_added.strftime('%d-%b-%Y')}")
    
    # Footer
    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, 50, "School Stamp: _________________________")
    pdf.drawString(300, 50, "Parent's Signature: _________________________")
    pdf.drawString(50, 30, "Generated on: " + timezone.now().strftime('%Y-%m-%d %H:%M'))
    
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

def calculate_grade(score):
    if score >= 90: return 'A+'
    elif score >= 80: return 'A'
    elif score >= 70: return 'B'
    elif score >= 60: return 'C'
    elif score >= 50: return 'D'
    else: return 'F'

def get_remark(score):
    if score >= 90: return 'Excellent'
    elif score >= 80: return 'Very Good'
    elif score >= 70: return 'Good'
    elif score >= 60: return 'Satisfactory'
    elif score >= 50: return 'Needs Improvement'
    else: return 'Poor'


# academics/utils.py
def calculate_final_grade(subject_grade):
    """Calculate final grade from all assessment components"""
    results = subject_grade.result_set.all()
    if not results:
        return 0, 'F'
    
    total_weighted_score = sum(result.weighted_score for result in results)
    total_possible_weight = sum(result.exam_type.weight for result in results)
    
    # Calculate final score (scaled to 100 if weights don't total 100)
    if total_possible_weight > 0:
        final_score = (total_weighted_score / total_possible_weight) * 100
    else:
        final_score = 0
    
    # Calculate grade
    grade = subject_grade.calculate_grade(final_score)
    
    return final_score, grade