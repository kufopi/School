from django.db import models
from core.models import User

class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    admission_date = models.DateField()
    current_class = models.ForeignKey('academics.Class', on_delete=models.SET_NULL, null=True)
    photo = models.ImageField(upload_to='students/photos/', blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

class StudentMedicalHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    condition = models.CharField(max_length=100)
    description = models.TextField()
    diagnosed_date = models.DateField()
    treatment = models.TextField(blank=True)
    is_chronic = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student} - {self.condition}"
    

class StudentHealthRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    record_date = models.DateField()
    height = models.DecimalField(max_digits=4, decimal_places=1, help_text="Height in cm")
    weight = models.DecimalField(max_digits=4, decimal_places=1, help_text="Weight in kg")
    bmi = models.DecimalField(max_digits=4, decimal_places=1, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Calculate BMI when saving
        if self.height and self.weight:
            self.bmi = self.weight / ((self.height/100) ** 2)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-record_date']

class BehaviorAssessment(models.Model):
    ASSESSMENT_CHOICES = [
        (1, 'Needs Improvement'),
        (2, 'Developing'),
        (3, 'Satisfactory'),
        (4, 'Good'),
        (5, 'Excellent')
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    assessment_date = models.DateField(auto_now_add=True)
    assessed_by = models.ForeignKey('staff.Teacher', on_delete=models.SET_NULL, null=True)
    
    # Skill Categories
    participation = models.PositiveSmallIntegerField(
        choices=ASSESSMENT_CHOICES,
        help_text="Class engagement, teamwork"
    )
    responsibility = models.PositiveSmallIntegerField(
        choices=ASSESSMENT_CHOICES,
        help_text="Completing assignments, following rules"
    )
    creativity = models.PositiveSmallIntegerField(
        choices=ASSESSMENT_CHOICES,
        help_text="Thinking skills, innovation"
    )
    cooperation = models.PositiveSmallIntegerField(
        choices=ASSESSMENT_CHOICES,
        help_text="Social skills, respect for others"
    )
    
    class Meta:
        unique_together = ('student', 'term')
        ordering = ['-term__start_date']

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    days_present = models.PositiveSmallIntegerField(default=0)
    days_absent = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        unique_together = ('student', 'term')
        
    @property
    def attendance_rate(self):
        total = self.days_present + self.days_absent
        return (self.days_present / total) * 100 if total > 0 else 0