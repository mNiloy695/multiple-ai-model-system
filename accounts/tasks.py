from celery import shared_task
from .utils import send_otp_email  # wherever your send_otp_email is

@shared_task
def send_otp_email_task(email, otp, user="User", task="Account Verification"):
    send_otp_email(email, otp, user, task)