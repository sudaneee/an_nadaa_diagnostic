from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile

class UserRegistrationForm(UserCreationForm):
    """Form for creating new users"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Add placeholders
        self.fields['username'].widget.attrs.update({'placeholder': 'Enter username'})
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Enter first name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Enter last name'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter email address'})
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'Enter phone number'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm password'})

class UserEditForm(forms.ModelForm):
    """Form for editing users"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Make is_active a checkbox
        self.fields['is_active'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})

class UserProfileForm(forms.ModelForm):
    """Form for user profile with photo and signature"""
    class Meta:
        model = UserProfile
        fields = ['passport_photo', 'signature', 'department', 'employee_id', 'address']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'passport_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'signature': forms.FileInput(attrs={'class': 'form-control'}),
        }