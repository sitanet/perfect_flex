from django import forms
from accounts_admin.models import Account

from company.models import Company
from .models import User, UserProfile
from .validators import allow_only_images_validator


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter First Name', 'required': 'required'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter First Name', 'required': 'required'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter First Name', 'required': 'required'}))
    # middle_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Middle Name', 'required': 'required'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Last Name', 'required': 'required'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Username ', 'required': 'required'}))
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Email', 'required': 'required'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Phone Number', 'required': 'required'}))
    # gender = forms.CharField(widget=forms.TextInput(attrs={}))
    # staff_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Staff ID', 'required': 'required'}))
    # role = forms.Select()

    class Meta:
        model = User
        fields = ['profile_picture','first_name', 'last_name', 'username', 'email', 'role', 'phone_number', 'password','branch','cashier_gl','cashier_ac']

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Password does not match!"
            )
        


class EdituserForm(forms.ModelForm):

     class Meta:
        model = User
        fields = ['profile_picture','first_name', 'last_name', 'username', 'email', 'role', 'phone_number','branch','cashier_gl','cashier_ac']
       
class UserProfileForm(forms.ModelForm):
   

    
    
    class Meta:
        model = UserProfile
        fields = []

class UserProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture']




