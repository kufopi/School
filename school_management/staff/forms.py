from django import forms
from .models import Teacher
from core.models import User

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['staff_id', 'qualification', 'specialization', 'date_employed']