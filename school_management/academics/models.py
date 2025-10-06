from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Class(models.Model):
    ARM_CHOICES = (
        ('Alpha', 'Alpha'),
        ('Beta', 'Beta'),
        ('Gamma', 'Gamma'),
        ('Delta', 'Delta'),
    )
    name = models.CharField(max_length=50)  # "Primary 1", "Primary 2"
    short_name = models.CharField(max_length=10)  # "P1", "P2"
    level = models.PositiveSmallIntegerField()  # 1-6 for primary school
    arm = models.CharField(max_length=20, blank=True, null=True, choices=ARM_CHOICES,default="Alpha")  # "Alpha", "Beta", "Gamma"
    
    class Meta:
        unique_together = ('level', 'arm')  # Prevents duplicate P1 Alpha
        ordering = ['level', 'arm']
    
    def __str__(self):
        if self.arm:
            return f"{self.name} {self.arm}"
        return self.name
    
    @property
    def full_name(self):
        """Returns the complete class name including arm"""
        if self.arm:
            return f"{self.name} {self.arm}"
        return self.name
    
    @property
    def display_code(self):
        """Returns short display code like P1A, P1B"""
        if self.arm:
            return f"{self.short_name}{self.arm[0]}"  # P1A, P1B
        return self.short_name

# Example usage:
# Class(name="Primary 1", short_name="P1", level=1, arm="Alpha")  -> "Primary 1 Alpha"
# Class(name="Primary 1", short_name="P1", level=1, arm="Beta")   -> "Primary 1 Beta"
# Class(name="Primary 6", short_name="P6", level=6, arm=None)     -> "Primary 6"

class ClassSubject(models.Model):
    class_info = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('staff.Teacher', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('class_info', 'subject')
    
    def __str__(self):
        return f"{self.class_info} - {self.subject}"

class ExamType(models.Model):
    name = models.CharField(max_length=50)  # e.g., "CA", "Exam"
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage weight in final score (e.g., 40 for CA, 60 for Exam)"
    )
    max_score = models.PositiveSmallIntegerField(
        default=100,
        help_text="Maximum raw score for this exam type (e.g., 40 for CA, 60 for Exam)"
    )
    is_final = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['weight']
    
    def __str__(self):
        return f"{self.name} ({self.weight}% of 100, max {self.max_score})"

# academics/models.py
class TermReport(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('student', 'term')
    
    def __str__(self):
        return f"Term Report for {self.student} - {self.term}"
    
    def clean(self):
        # In TermReport model or a form
        results = self.result_set.all()
        total_weight = sum(r.exam_type.weight for r in results)
        if total_weight != 100:
            raise ValidationError(f"Exam weights must sum to 100%, current sum: {total_weight}%")
    
    def calculate_subject_grade(self, score):
        """Calculate letter grade based on total score."""
        score = float(score)
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B'
        elif score >= 60: return 'C'
        elif score >= 50: return 'D'
        else: return 'F'
    
    def get_subject_results(self):
        """Get aggregated results by subject."""
        results = self.result_set.all().select_related('subject', 'exam_type')
        subject_results = {}
        
        for result in results:
            subject_id = result.subject.id
            if subject_id not in subject_results:
                subject_results[subject_id] = {
                    'subject': result.subject,
                    'results': [],
                    'total_score': 0,
                    'grade': 'F'
                }
            subject_results[subject_id]['results'].append(result)
        
        for subject_id, data in subject_results.items():
            # CORRECTED CALCULATION
            total_weighted_score = sum(
                (float(r.score) / float(r.exam_type.max_score)) * float(r.exam_type.weight)
                for r in data['results']
            )
            
            # Total possible weight (should typically be 100 if all exam types are included)
            total_weight = sum(r.exam_type.weight for r in data['results'])
            
            if total_weight > 0:
                # This gives the final percentage score out of 100
                data['total_score'] = total_weighted_score
                data['grade'] = self.calculate_subject_grade(data['total_score'])
        
        return subject_results.values()

class SubjectGrade(models.Model):
    """Final computed grade for each subject in a term report"""
    report = models.ForeignKey(TermReport, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, blank=True)
    position = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('report', 'subject')
        ordering = ['subject__name']
    
    def __str__(self):
        return f"{self.subject} - {self.final_score}% ({self.grade})"
    
    def calculate_grade(self, score):
        """Calculate letter grade based on score"""
        score = float(score)
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B'
        elif score >= 60: return 'C'
        elif score >= 50: return 'D'
        else: return 'F'



class Result(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    term_report = models.ForeignKey('TermReport', on_delete=models.CASCADE, null=True, blank=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Raw score (e.g., out of 40 for CA, 60 for Exam)"
    )
    date_recorded = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey('staff.Teacher', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('student', 'term', 'subject', 'exam_type')
        ordering = ['exam_type__weight']
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam_type}: {self.score}/{self.exam_type.max_score}"
    
    def clean(self):
        if self.score > self.exam_type.max_score:
            raise ValidationError(f"Score cannot exceed {self.exam_type.max_score} for {self.exam_type.name}")
    
    @property
    def weighted_score(self):
        return (float(self.score) / float(self.exam_type.max_score)) * float(self.exam_type.weight)


###############################################################################



class ReportComment(models.Model):
    COMMENT_TYPE_CHOICES = (
        ('teacher', 'Class Teacher Comment'),
        ('principal', 'Principal Comment'),
    )
    
    report = models.ForeignKey(TermReport, on_delete=models.CASCADE)
    comment_type = models.CharField(max_length=10, choices=COMMENT_TYPE_CHOICES)
    comment = models.TextField()
    date_added = models.DateField(auto_now_add=True)
    added_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('report', 'comment_type')  # One per type per report
    
    def __str__(self):
        return f"{self.get_comment_type_display()} for {self.report}"
    

class PredefinedComment(models.Model):
    COMMENT_TYPE_CHOICES = (
        ('teacher', 'Class Teacher Comment'),
        ('principal', 'Principal Comment'),
    )
    
    comment_type = models.CharField(max_length=10, choices=COMMENT_TYPE_CHOICES)
    text = models.TextField()
    
    def __str__(self):
        return f"{self.get_comment_type_display()}: {self.text[:50]}..."