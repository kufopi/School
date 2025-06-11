from django import forms
from .models import Subject, Result, ReportComment

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'subject', 'exam_type', 'term', 'score']

class ReportCommentForm(forms.ModelForm):
    class Meta:
        model = ReportComment
        fields = ['comment_type', 'comment']