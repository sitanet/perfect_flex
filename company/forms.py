from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'



from django import forms
from .models import Company

class EndSession(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['session_date', 'session_status']

    SESSION_STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    )
    session_status = forms.ChoiceField(choices=SESSION_STATUS_CHOICES, widget=forms.Select)
