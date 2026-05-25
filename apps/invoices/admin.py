from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment, Referral


# ── Referral ───────────────────────────────────────────────────────────────────

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']


# ── Invoice ────────────────────────────────────────────────────────────────────

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['total_price']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['payment_date', 'received_by']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'full_name', 'phone_number', 'sex', 'age',
        'total_amount', 'payment_method', 'status', 'referral', 'created_by', 'created_at',
    ]
    list_filter = ['status', 'payment_method', 'sex', 'created_at', 'referral', 'created_by']
    search_fields = [
        'invoice_number', 'surname', 'first_name', 'other_names', 'phone_number',
    ]
    readonly_fields = ['invoice_number', 'qr_code', 'total_amount', 'amount_paid', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline, PaymentInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Invoice', {
            'fields': ('invoice_number', 'status', 'created_by', 'created_at', 'updated_at'),
        }),
        ('Patient', {
            'fields': ('surname', 'first_name', 'other_names', 'age', 'sex', 'phone_number'),
        }),
        ('Referral', {
            'fields': ('referral',),
        }),
        ('Financial', {
            'fields': ('discount', 'total_amount', 'amount_paid', 'payment_method', 'reference_number'),
        }),
        ('Other', {
            'fields': ('notes', 'qr_code'),
        }),
    )


# ── Payment ────────────────────────────────────────────────────────────────────

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_method', 'reference_number', 'payment_date', 'received_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'invoice__surname', 'invoice__first_name', 'reference_number']
    readonly_fields = ['payment_date']
    date_hierarchy = 'payment_date'
