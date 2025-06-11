from django.db import models

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
    name = models.CharField(max_length=50)  # "First Test", "Mid-Term", "End of Term"
    weight = models.PositiveSmallIntegerField()  # Percentage weight in final score
    
    def __str__(self):
        return self.name


# academics/models.py
class TermReport(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('student', 'term')
    
    def __str__(self):
        return f"Term Report for {self.student} - {self.term}"


class Result(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    date_recorded = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey('staff.Teacher', on_delete=models.SET_NULL, null=True)
    report = models.ForeignKey(TermReport, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'subject', 'exam_type', 'term')
    
    def __str__(self):
        return f"{self.student} - {self.subject} ({self.exam_type}): {self.score}"



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