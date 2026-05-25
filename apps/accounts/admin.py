from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, UserProfile, CentreProfile


@admin.register(CentreProfile)
class CentreProfileAdmin(admin.ModelAdmin):
    """Singleton admin — edit the one Centre Profile record."""
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'tagline', 'logo', 'logo_preview'),
        }),
        ('Contact & Location', {
            'fields': ('address', 'phone', 'email'),
        }),
    )
    readonly_fields = ['logo_preview']

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:120px;border:1px solid #ddd;padding:4px"/>', obj.logo.url)
        return "No logo uploaded yet."
    logo_preview.short_description = "Preview"

    def has_add_permission(self, request):
        return not CentreProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # never delete the singleton

    def changelist_view(self, request, extra_context=None):
        # Skip the list page — go straight to the edit form
        obj, _ = CentreProfile.objects.get_or_create(pk=1, defaults={
            'name': 'An-Nadaa Diagnostic Centre',
            'address': 'Abuja, Nigeria',
            'phone': '+234 000 000 0000',
        })
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse('admin:accounts_centreprofile_change', args=[obj.pk])
        )

class UserProfileInline(admin.StackedInline):
    """Inline profile editing in user admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Personal Information', {
            'fields': ('passport_photo', 'signature', 'department', 'employee_id', 'address')
        }),
    )

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model with role and profile"""
    
    list_display = ['username', 'email', 'full_name', 'role_badge', 'phone_number', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact Information', {
            'fields': ('role', 'phone_number'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Contact Information', {
            'fields': ('role', 'phone_number', 'first_name', 'last_name', 'email'),
        }),
    )
    
    inlines = [UserProfileInline]
    
    def full_name(self, obj):
        """Display full name"""
        return obj.get_full_name() or obj.username
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'first_name'
    
    def role_badge(self, obj):
        """Display role with color badge"""
        colors = {
            'ADMIN': 'danger',
            'CASHIER': 'success',
            'DOCTOR': 'primary',
            'LAB_TECH': 'info',
        }
        color = colors.get(obj.role, 'secondary')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            {
                'danger': '#dc3545',
                'success': '#28a745',
                'primary': '#007bff',
                'info': '#17a2b8',
                'secondary': '#6c757d'
            }.get(color, '#6c757d'),
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('profile')
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    
    list_display = ['user', 'employee_id', 'department', 'has_photo', 'has_signature', 'created_at']
    list_filter = ['department', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'employee_id']
    readonly_fields = ['created_at', 'updated_at', 'photo_preview', 'signature_preview']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'employee_id', 'department')
        }),
        ('Personal Information', {
            'fields': ('address',)
        }),
        ('Images', {
            'fields': ('passport_photo', 'photo_preview', 'signature', 'signature_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_photo(self, obj):
        """Check if user has passport photo"""
        return bool(obj.passport_photo)
    has_photo.boolean = True
    has_photo.short_description = 'Photo'
    
    def has_signature(self, obj):
        """Check if user has signature"""
        return bool(obj.signature)
    has_signature.boolean = True
    has_signature.short_description = 'Signature'
    
    def photo_preview(self, obj):
        """Display photo preview in admin"""
        if obj.passport_photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 50%;" />',
                obj.passport_photo.url
            )
        return format_html('<span style="color: gray;">No photo uploaded</span>')
    photo_preview.short_description = 'Photo Preview'
    
    def signature_preview(self, obj):
        """Display signature preview in admin"""
        if obj.signature:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 200px;" />',
                obj.signature.url
            )
        return format_html('<span style="color: gray;">No signature uploaded</span>')
    signature_preview.short_description = 'Signature Preview'