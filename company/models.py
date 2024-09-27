from django.utils import timezone
from django.db import models

class Company(models.Model):
    company_name = models.CharField(max_length=100, null=True, blank=True)
    branch_code = models.CharField(max_length=5)
    branch_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    office_address = models.CharField(max_length=100)
    contact_phone_no = models.CharField(max_length=100)
    session_date = models.DateField(null=True, blank=True)
    system_date_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField()
    expiration_date = models.DateField()
    license_key = models.CharField(max_length=50)
    session_status = models.CharField(max_length=10, null=True, blank=True)
    # New fields
    # company_name = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
            return str(self.branch_code)
    