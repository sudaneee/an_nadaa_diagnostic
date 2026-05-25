from django.contrib import admin
from .models import Report, ReportParameter, ReportAttachment


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display  = ['report_number', 'client_name', 'service', 'signatory', 'created_by', 'created_at']
    list_filter   = ['service', 'created_at']
    search_fields = [
        'report_number',
        'invoice__surname', 'invoice__first_name', 'invoice__phone_number',
        'service__name', 'signatory',
    ]
    readonly_fields = ['report_number', 'parameters']

    fieldsets = (
        ('Basic Information', {
            'fields': ('report_number', 'invoice', 'invoice_item', 'service'),
        }),
        ('Report Content', {
            'fields': ('parameters', 'clinical_notes', 'lab_notes'),
        }),
        ('Signatory', {
            'fields': ('signatory', 'created_by'),
        }),
    )


@admin.register(ReportParameter)
class ReportParameterAdmin(admin.ModelAdmin):
    list_display  = ['service', 'name', 'parameter_type', 'unit', 'normal_range', 'required', 'order']
    list_filter   = ['service', 'parameter_type']
    search_fields = ['name', 'service__name']


@admin.register(ReportAttachment)
class ReportAttachmentAdmin(admin.ModelAdmin):
    list_display = ['report', 'description', 'uploaded_by', 'uploaded_at']
    list_filter  = ['uploaded_at']
