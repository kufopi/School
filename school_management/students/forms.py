from django import forms
from .models import Student,StudentMedicalHistory
from core.models import User

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        exclude = ['user', 'student_id']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_class'].queryset = self.fields['current_class'].queryset.order_by('level')

class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = StudentMedicalHistory
        fields = ['condition', 'description', 'diagnosed_date', 'treatment', 'is_chronic']



from .models import (
    StudentHealthRecord, 
    BehaviorAssessment,
    
    AttendanceRecord
)
from academics.models import Result

class StudentHealthForm(forms.ModelForm):
    class Meta:
        model = StudentHealthRecord
        fields = ['record_date', 'height', 'weight', 'notes']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'})
        }

class BehaviorAssessmentForm(forms.ModelForm):
    class Meta:
        model = BehaviorAssessment
        fields = ['participation', 'responsibility', 'creativity', 'cooperation']
        widgets = {
            'participation': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'responsibility': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'creativity': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'cooperation': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['score', 'exam_type']
        
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['days_present', 'days_absent']