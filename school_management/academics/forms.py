from django import forms
from .models import Subject, Result, ReportComment, ExamType
from django.core.exceptions import ValidationError


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'term', 'subject', 'exam_type', 'score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 0, 'step': 0.5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'exam_type' in self.data:
            try:
                exam_type_id = int(self.data.get('exam_type'))
                exam_type = ExamType.objects.get(id=exam_type_id)
                self.fields['score'].widget.attrs['max'] = exam_type.max_score
            except (ValueError, ExamType.DoesNotExist):
                pass

    def clean_score(self):
        score = self.cleaned_data['score']
        exam_type = self.cleaned_data.get('exam_type')
        if exam_type and score > exam_type.max_score:
            raise ValidationError(f"Score cannot exceed {exam_type.max_score} for {exam_type.name}")
        return score

class ReportCommentForm(forms.ModelForm):
    class Meta:
        model = ReportComment
        fields = ['comment_type', 'comment']