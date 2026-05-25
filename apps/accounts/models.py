from django.db import models
from django.contrib.auth.models import AbstractUser


class CentreProfile(models.Model):
    """Singleton that holds the diagnostic centre's identity shown on printed reports."""

    name     = models.CharField(max_length=200, default="An-Nadaa Diagnostic Centre")
    tagline  = models.CharField(max_length=300, blank=True,
                                help_text="Short motto, e.g. 'Your Health, Our Priority'")
    address  = models.TextField(help_text="Full address printed on reports")
    phone    = models.CharField(max_length=150,
                                help_text="Phone number(s) — use commas for multiple")
    email    = models.EmailField(blank=True)
    logo     = models.ImageField(upload_to='centre/', blank=True, null=True,
                                 help_text="Logo printed at the top of every report")

    class Meta:
        verbose_name        = "Centre Profile"
        verbose_name_plural = "Centre Profile"  # keeps admin sidebar label singular

    def __str__(self):
        return self.name

    # Enforce singleton: always pk = 1
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_profile(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'name': 'An-Nadaa Diagnostic Centre',
            'address': 'Abuja, Nigeria',
            'phone': '+234 000 000 0000',
        })
        return obj


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('CASHIER', 'Cashier'),
        ('DOCTOR', 'Doctor'),
        ('LAB_TECH', 'Lab Technician'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CASHIER')
    phone_number = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'ADMIN'
    
    @property
    def is_cashier(self):
        return self.role == 'CASHIER'
    
    @property
    def is_doctor(self):
        return self.role == 'DOCTOR'
    
    @property
    def is_lab_tech(self):
        return self.role == 'LAB_TECH'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    passport_photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"