from django.db import models
from core.models import User

class Parent(models.Model):
    RELATIONSHIP_CHOICES = (
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    phone=models.CharField(max_length=15)
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.relationship})"

class ParentStudent(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('parent', 'student')
    
    def __str__(self):
        return f"{self.parent} -> {self.student}"