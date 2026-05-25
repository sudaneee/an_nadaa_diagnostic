from django import forms
from .models import Service, ServiceCategory

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'category', 'price', 'is_active', 'requires_report', 'report_template']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_report': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'report_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }
        help_texts = {
            'report_template': 'JSON format. Leave empty for auto-generated template based on service name.'
        }