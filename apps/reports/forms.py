from django import forms
from .models import Report, ReportParameter


class ReportForm(forms.ModelForm):
    """
    Used for creating and editing a report.
    Dynamically adds parameter fields based on the service.
    """

    class Meta:
        model  = Report
        fields = ['signatory', 'clinical_notes', 'lab_notes']
        widgets = {
            'signatory': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Dr. Aminu Musa, MBBS, FWACP',
            }),
            'clinical_notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Clinical notes / history…',
            }),
            'lab_notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Technical / laboratory notes…',
            }),
        }
        labels = {
            'signatory': 'Result Signatory',
        }

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)

        if self.service:
            for param in ReportParameter.objects.filter(service=self.service):
                fname = f'param_{param.id}'

                if param.parameter_type == 'text':
                    field = forms.CharField(
                        required=param.required,
                        widget=forms.TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': param.name,
                        }),
                    )
                elif param.parameter_type == 'textarea':
                    field = forms.CharField(
                        required=param.required,
                        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                    )
                elif param.parameter_type == 'number':
                    field = forms.FloatField(
                        required=param.required,
                        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
                    )
                elif param.parameter_type == 'select':
                    field = forms.ChoiceField(
                        choices=[('', '— Select —')] + [(o, o) for o in param.options],
                        required=param.required,
                        widget=forms.Select(attrs={'class': 'form-select'}),
                    )
                elif param.parameter_type == 'checkbox':
                    field = forms.BooleanField(
                        required=False,
                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                    )
                else:
                    field = forms.CharField(
                        required=param.required,
                        widget=forms.TextInput(attrs={'class': 'form-control'}),
                    )

                hints = []
                if param.unit:
                    hints.append(f'Unit: {param.unit}')
                if param.normal_range:
                    hints.append(f'Normal: {param.normal_range}')
                field.help_text = ' | '.join(hints)
                field.label     = param.name

                # Pre-populate when editing an existing report
                if self.instance and self.instance.pk:
                    field.initial = self.instance.parameters.get(str(param.id), '')

                self.fields[fname] = field
