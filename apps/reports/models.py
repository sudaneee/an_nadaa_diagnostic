from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.invoices.models import Invoice, InvoiceItem
from apps.services.models import Service


class Report(models.Model):
    report_number = models.CharField(max_length=50, unique=True, editable=False)

    # Invoice link — the authoritative source of all patient information
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT,
        null=True, blank=True, related_name='reports',
    )
    invoice_item = models.ForeignKey(
        InvoiceItem, on_delete=models.PROTECT,
        null=True, blank=True, related_name='reports',
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name='reports',
    )

    # Results — JSON keyed by ReportParameter.id
    parameters = models.JSONField(
        default=dict, help_text='Parameter values entered by the lab technician',
    )

    # Narrative notes (null=True kept for backward-compat with existing rows)
    clinical_notes = models.TextField(blank=True, null=True)
    lab_notes      = models.TextField(blank=True, null=True)

    # Who signs the report (free-text: name + qualifications)
    signatory = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Name and qualifications of the result signatory, "
                  "e.g. Dr. Aminu Musa, MBBS, FWACP",
    )

    # Staff
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_reports',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    # ── Patient info (derived from linked invoice) ────────────────────────────

    @property
    def client_name(self):
        return self.invoice.full_name if self.invoice else 'Unknown'

    @property
    def client_phone(self):
        return self.invoice.phone_number if self.invoice else ''

    @property
    def client_age(self):
        return self.invoice.age if self.invoice else ''

    @property
    def client_sex(self):
        return self.invoice.get_sex_display() if self.invoice else ''

    # ── Auto-numbering ────────────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        if not self.report_number:
            today    = timezone.now()
            date_str = today.strftime('%Y%m%d')
            name_lower = self.service.name.lower()

            if 'malaria' in name_lower:
                code = 'ML'
            elif 'blood count' in name_lower or 'fbc' in name_lower:
                code = 'FBC'
            elif 'xray' in name_lower or 'x-ray' in name_lower:
                code = 'XR'
            elif 'ultrasound' in name_lower:
                code = 'US'
            elif 'urinalysis' in name_lower:
                code = 'UA'
            else:
                code = self.service.name[:3].upper().replace(' ', '')

            last = (
                Report.objects
                .filter(report_number__startswith=f'{code}-{date_str}-')
                .order_by('-report_number')
                .first()
            )
            try:
                seq = int(last.report_number.split('-')[-1]) + 1 if last else 1
            except (ValueError, AttributeError):
                seq = 1

            self.report_number = f'{code}-{date_str}-{seq:04d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.report_number} — {self.client_name} — {self.service.name}'


class ReportParameter(models.Model):
    """Defines the structured fields a service's report should capture."""

    PARAMETER_TYPES = [
        ('text',     'Text Input'),
        ('textarea', 'Text Area'),
        ('number',   'Number'),
        ('select',   'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('date',     'Date'),
    ]

    service        = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='report_parameters')
    name           = models.CharField(max_length=100)
    parameter_type = models.CharField(max_length=20, choices=PARAMETER_TYPES, default='text')
    unit           = models.CharField(max_length=50, blank=True, null=True)
    normal_range   = models.CharField(max_length=100, blank=True, null=True)
    options        = models.JSONField(default=list, blank=True,
                                     help_text='For select type: list of options')
    required       = models.BooleanField(default=True)
    order          = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.service.name} — {self.name}'


class ReportAttachment(models.Model):
    """Images, scan files, or any file attached to a report."""

    report      = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='attachments')
    file        = models.FileField(upload_to='report_attachments/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.report.report_number} — {self.description or "Attachment"}'
