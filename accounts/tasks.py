from celery import shared_task
from .utils import send_the_email  # wherever your send_otp_email is
from django.conf import settings
@shared_task
def send_otp_email_task(subject,user_email,message,message_type='registration'):
    
        send_the_email(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email]
            
            # fail_silently=False,
        )