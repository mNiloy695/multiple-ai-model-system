from celery import shared_task
from .utils import send_the_email
from django.conf import settings

@shared_task(bind=True)  # bind=True gives you access to self.retry()
def send_otp_email_task(self, subject, user_email, message, message_type='registration'):
    try:
        send_the_email(
            subject=subject,
            message=message,
            user_email=user_email
        )
    except Exception as e:
        # retry the task after 60 seconds if it fails
        raise self.retry(exc=e, countdown=60)
    
from celery import shared_task
from django.conf import settings

@shared_task
def debug_env():
    print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
    return settings.EMAIL_HOST_USER