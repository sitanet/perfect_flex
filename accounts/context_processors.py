# accounts/context_processors.py

from django.utils import timezone
from .models import Company

def soon_to_expire(request):
    soon_expire_message = None
    if request.user.is_authenticated:
        try:
            company = Company.objects.get(branch_code=request.user.branch)
            expiration_date = company.expiration_date
            today = timezone.now().date()
            # Check if expiration date is within 30 days from today
            if expiration_date <= today + timezone.timedelta(days=30) and expiration_date >= today:
                soon_expire_message = "Your company's license will expire soon. Please contact your vendor."
        except Company.DoesNotExist:
            soon_expire_message = "Company details not found. Please contact your vendor."
    return {'soon_expire_message': soon_expire_message}
