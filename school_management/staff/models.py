from django.db import models
from core.models import User

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True)
    qualification = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    date_employed = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"

class ClassTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey('academics.Class', on_delete=models.CASCADE)
    academic_session = models.ForeignKey('core.SchoolSession', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('class_assigned', 'academic_session')
    
    def __str__(self):
        return f"{self.teacher} - {self.class_assigned} ({self.academic_session})"