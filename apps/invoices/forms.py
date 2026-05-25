from django import forms
from .models import Invoice, Payment, Referral


class InvoiceCreateForm(forms.Form):
    """
    Single comprehensive form — captures patient info, referral, discount,
    and payment in one step.  Services are handled as POST arrays in the view.
    """

    # ── Patient Information ────────────────────────────────────────────────────
    surname = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Mohammed',
            'autofocus': True,
        }),
    )
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Ibrahim',
        }),
    )
    other_names = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Middle / other name (optional)',
        }),
    )
    age = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 35 or 6m',
        }),
    )
    sex = forms.ChoiceField(
        choices=Invoice.SEX_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08012345678',
        }),
    )

    # ── Referral ───────────────────────────────────────────────────────────────
    referral = forms.ModelChoiceField(
        queryset=Referral.objects.filter(is_active=True).order_by('category', 'name'),
        required=False,
        empty_label='— Walk-in / None —',
        widget=forms.Select(attrs={'class': 'form-select referral-select'}),
    )

    # ── Financial ──────────────────────────────────────────────────────────────
    discount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'id': 'id_discount',
        }),
    )

    # ── Payment ────────────────────────────────────────────────────────────────
    payment_method = forms.ChoiceField(
        choices=Invoice.PAYMENT_METHODS,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_payment_method',
        }),
    )
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Transaction / receipt reference',
            'id': 'id_reference_number',
        }),
    )

    # ── Notes ──────────────────────────────────────────────────────────────────
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes…',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        ref = cleaned.get('reference_number', '').strip()
        if method in ('TRANSFER', 'CARD') and not ref:
            self.add_error(
                'reference_number',
                'Please enter a reference number for Transfer / Card payments.'
            )
        return cleaned
