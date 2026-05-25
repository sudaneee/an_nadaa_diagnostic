import django_filters
from django.db.models import Q

from .models import Invoice, Referral
from apps.accounts.models import User
from apps.services.models import Service


class InvoiceFilter(django_filters.FilterSet):

    # ── Text searches ──────────────────────────────────────────────────────────
    invoice_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Invoice #',
        widget=__import__('django').forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': 'INV-...'}
        ),
    )
    client_name = django_filters.CharFilter(
        method='filter_client_name',
        label='Patient Name',
        widget=__import__('django').forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': 'Surname or first name'}
        ),
    )
    phone_number = django_filters.CharFilter(
        field_name='phone_number',
        lookup_expr='icontains',
        label='Phone',
        widget=__import__('django').forms.TextInput(
            attrs={'class': 'form-control form-control-sm', 'placeholder': '080...'}
        ),
    )

    # ── Date range ─────────────────────────────────────────────────────────────
    date_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte',
        label='From',
        widget=__import__('django').forms.DateInput(
            attrs={'class': 'form-control form-control-sm', 'type': 'date'}
        ),
    )
    date_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte',
        label='To',
        widget=__import__('django').forms.DateInput(
            attrs={'class': 'form-control form-control-sm', 'type': 'date'}
        ),
    )

    # ── Relational ─────────────────────────────────────────────────────────────
    cashier = django_filters.ModelChoiceFilter(
        field_name='created_by',
        queryset=User.objects.filter(role__in=['CASHIER', 'ADMIN']).order_by('first_name'),
        label='Cashier',
        empty_label='All Cashiers',
        widget=__import__('django').forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    payment_method = django_filters.ChoiceFilter(
        choices=[('', 'All Methods')] + list(Invoice.PAYMENT_METHODS),
        label='Payment Method',
        empty_label=None,
        widget=__import__('django').forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    service = django_filters.ModelChoiceFilter(
        field_name='items__service',
        queryset=Service.objects.filter(is_active=True).order_by('name'),
        label='Examination',
        empty_label='All Examinations',
        widget=__import__('django').forms.Select(attrs={'class': 'form-select form-select-sm'}),
        distinct=True,
    )
    referral = django_filters.ModelChoiceFilter(
        queryset=Referral.objects.all().order_by('name'),
        label='Referral Source',
        empty_label='All Referrals',
        widget=__import__('django').forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    status = django_filters.ChoiceFilter(
        choices=[('', 'All Status')] + list(Invoice.STATUS_CHOICES),
        label='Status',
        empty_label=None,
        widget=__import__('django').forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )

    class Meta:
        model = Invoice
        fields: list = []

    def filter_client_name(self, queryset, name, value):
        return queryset.filter(
            Q(surname__icontains=value)
            | Q(first_name__icontains=value)
            | Q(other_names__icontains=value)
        )
