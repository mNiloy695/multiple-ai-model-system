from django.core.mail import send_mail
from django.conf import settings

def send_the_email(subject,user_email,message,message_type='registration'):
    # subject = "Welcome to MultiAI Platform 🚀"
  
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            # fail_silently=False,
        )
 