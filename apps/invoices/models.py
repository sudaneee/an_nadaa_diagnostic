import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.services.models import Service


class Referral(models.Model):
    CATEGORY_CHOICES = [
        ('HOSPITAL', 'Hospital'),
        ('CLINIC', 'Clinic'),
        ('DOCTOR', 'Doctor'),
        ('ORGANIZATION', 'Organization'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Referral Source'
        verbose_name_plural = 'Referral Sources'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('TRANSFER', 'Bank Transfer'),
        ('CARD', 'Card'),
    ]

    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    # Auto-generated invoice number
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)

    # Patient information (inline — no persistent client profile required)
    surname = models.CharField(max_length=100, verbose_name='Surname')
    first_name = models.CharField(max_length=100, verbose_name='First Name')
    other_names = models.CharField(max_length=100, blank=True, verbose_name='Other Names')
    age = models.CharField(max_length=10, verbose_name='Age')
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, verbose_name='Sex')
    phone_number = models.CharField(max_length=20, verbose_name='Phone Number')

    # Referral source
    referral = models.ForeignKey(
        Referral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Referred By',
    )

    # Financial
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                   validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Payment (recorded at the point of creation)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    reference_number = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Reference number for Transfer or Card payments'
    )

    # Status — always PAID after creation; CANCELLED if voided
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')

    notes = models.TextField(blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_invoices',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    # ── Convenience helpers ────────────────────────────────────────────────────

    @property
    def full_name(self):
        parts = [self.surname, self.first_name]
        if self.other_names:
            parts.append(self.other_names)
        return ' '.join(parts)

    # Alias for templates that still use the old attribute name
    @property
    def client_name(self):
        return self.full_name

    # ── Auto-numbering ─────────────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            last = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{date_str}-'
            ).order_by('-invoice_number').first()

            if last:
                try:
                    seq = int(last.invoice_number.split('-')[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1

            self.invoice_number = f'INV-{date_str}-{seq:04d}'

        super().save(*args, **kwargs)

    # ── Financial helpers ──────────────────────────────────────────────────────

    def calculate_total(self):
        subtotal = sum(item.total_price for item in self.items.all())
        return max(subtotal - self.discount, 0)

    def update_total(self):
        self.total_amount = self.calculate_total()
        Invoice.objects.filter(pk=self.pk).update(total_amount=self.total_amount)

    def __str__(self):
        return f'{self.invoice_number} — {self.full_name}'


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.service.name} × {self.quantity}'


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('TRANSFER', 'Bank Transfer'),
        ('CARD', 'Card'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='processed_payments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return (
            f'{self.invoice.invoice_number} — '
            f'₦{self.amount} via {self.get_payment_method_display()}'
        )
