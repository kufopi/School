from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=100)
    organizer = models.ForeignKey('staff.Teacher', on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title