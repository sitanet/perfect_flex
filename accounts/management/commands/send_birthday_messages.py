from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import date
from accounts.models import Clents

class Command(BaseCommand):
    help = 'Sends birthday messages to customers'

    def handle(self, *args, **kwargs):
        today = date.today()
        customers = Clents.objects.filter(date_of_birth__day=today.day, date_of_birth__month=today.month)

        for customer in customers:
            subject = 'Happy Birthday, {}!'.format(customer.name)
            html_message = render_to_string('birthday_email.html', {'name': customer.name})
            plain_message = strip_tags(html_message)
            from_email = 'your@example.com'  # Replace with your email
            to_email = customer.email

            email = EmailMultiAlternatives(subject, plain_message, from_email, [to_email])
            email.attach_alternative(html_message, "text/html")
            email.send()

        self.stdout.write(self.style.SUCCESS('Birthday messages sent successfully'))
