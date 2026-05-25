from django.db import models
from django.core.validators import MinValueValidator

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Service Categories"
    
    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='services'
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    requires_report = models.BooleanField(
        default=False,
        help_text="Does this service require a medical report?"
    )
    report_template = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON template for report parameters"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - ₦{self.price}"
    
    def get_report_template(self):
        """Return the report template with default structure"""
        if self.report_template:
            return self.report_template
        
        # Default templates based on service name
        if 'malaria' in self.name.lower():
            return {
                'parameters': [
                    {'name': 'Malaria Parasite', 'type': 'select', 'options': ['Positive', 'Negative'], 'required': True},
                    {'name': 'Species', 'type': 'select', 'options': ['P. falciparum', 'P. vivax', 'P. ovale', 'P. malariae'], 'required': False},
                    {'name': 'Parasite Density', 'type': 'select', 'options': ['+', '++', '+++', '++++'], 'required': False},
                    {'name': 'Comments', 'type': 'textarea', 'required': False}
                ]
            }
        elif 'blood count' in self.name.lower() or 'fbc' in self.name.lower():
            return {
                'parameters': [
                    {'name': 'Hemoglobin', 'type': 'number', 'unit': 'g/dL', 'normal_range': '12-16', 'required': True},
                    {'name': 'WBC', 'type': 'number', 'unit': 'x10^3/μL', 'normal_range': '4-11', 'required': True},
                    {'name': 'RBC', 'type': 'number', 'unit': 'x10^6/μL', 'normal_range': '4.5-5.5', 'required': True},
                    {'name': 'Platelets', 'type': 'number', 'unit': 'x10^3/μL', 'normal_range': '150-450', 'required': True},
                    {'name': 'Comments', 'type': 'textarea', 'required': False}
                ]
            }
        elif 'x-ray' in self.name.lower() or 'xray' in self.name.lower():
            return {
                'parameters': [
                    {'name': 'Findings', 'type': 'textarea', 'required': True},
                    {'name': 'Impression', 'type': 'textarea', 'required': True},
                    {'name': 'Recommendations', 'type': 'textarea', 'required': False}
                ]
            }
        elif 'ultrasound' in self.name.lower():
            return {
                'parameters': [
                    {'name': 'Findings', 'type': 'textarea', 'required': True},
                    {'name': 'Measurements', 'type': 'textarea', 'required': False},
                    {'name': 'Impression', 'type': 'textarea', 'required': True},
                    {'name': 'Recommendations', 'type': 'textarea', 'required': False}
                ]
            }
        else:
            # Generic template
            return {
                'parameters': [
                    {'name': 'Findings', 'type': 'textarea', 'required': True},
                    {'name': 'Conclusion', 'type': 'textarea', 'required': True},
                    {'name': 'Remarks', 'type': 'textarea', 'required': False}
                ]
            }