from django.db import models
from django.contrib.auth.models import AbstractUser

SESS = [tuple([str(x)+'/'+str(x+1), str(x)+'/'+str(x+1)]) for x in range(2014,2070,1)]
TERM = (
    ('First Term','First Term'),
    ('Second Term','Second Term'),
    ('Third Term','Third Term'),
)

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    is_approved = models.BooleanField(default=False)  # For admin approval
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

class SchoolSession(models.Model):
    name = models.CharField(max_length=50,choices=SESS)  # e.g., "2023/2024 Academic Session"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class SchoolTerm(models.Model):
    session = models.ForeignKey(SchoolSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=50,choices=TERM)  # "First Term", "Second Term", etc.
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.session.name}"