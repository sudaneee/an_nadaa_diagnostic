from django.contrib import admin
from .models import ServiceCategory, Service

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_active', 'requires_report', 'created_at']
    list_filter = ['category', 'is_active', 'requires_report']
    search_fields = ['name']
    list_editable = ['price', 'is_active']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'price', 'is_active')
        }),
        ('Report Settings', {
            'fields': ('requires_report', 'report_template'),
            'classes': ('collapse',),
            'description': 'Configure if this service requires a medical report and define the report template'
        }),
    )