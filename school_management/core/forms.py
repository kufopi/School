from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User, SchoolSession,SchoolTerm

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'phone')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        # Add email validation if needed
        try:
            validate_email(username)
        except ValidationError:
            pass  # It's a username
        else:
            pass  # It's an email
        return username
    
from django import forms
from core.models import SchoolSession, SchoolTerm

class SchoolSessionForm(forms.ModelForm):
    class Meta:
        model = SchoolSession
        fields = ('name', 'start_date', 'end_date', 'is_current')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_current'].label = "Set as current session"

class SchoolTermForm(forms.ModelForm):
    class Meta:
        model = SchoolTerm
        fields = ('session', 'name', 'start_date', 'end_date', 'is_current')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_current'].label = "Set as current term"
        self.fields['session'].queryset = SchoolSession.objects.all()



