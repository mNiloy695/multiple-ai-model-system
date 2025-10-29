from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from smtplib import SMTPRecipientsRefused
from django.core.mail import BadHeaderError
from models import CustomUser

def send_otp_email(email, otp, user="User", task="Account Verification"):
    subject = "Your OTP Code"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    # Plain text fallback
    text_content = f"Hello {user}, your OTP for {task} is {otp}. It will expire in 3 minutes."

    # HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>Feet First OTP Verification</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f9fafb; color: #1f2937; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }}
        .otp-code {{ font-size: 48px; font-weight: 700; color: #1e40af; letter-spacing: 10px; text-align: center; }}
        .timer {{ display: block; text-align: center; background-color: #1e40af; color: #fff; padding: 6px 12px; border-radius: 100px; margin-top: 8px; font-size: 13px; font-weight: 500; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h2>Hello {user}!</h2>
            <p>Your verification code for <strong>{task}</strong> is:</p>
            <div class="otp-code">{otp}</div>
            <div class="timer">Expires in 3:00</div>
            <p>Enter this code to complete your verification. It will expire in 3 minutes.</p>
        </div>
    </body>
    </html>
    """

    print("Sending email...", text_content)

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except SMTPRecipientsRefused:
        print("⚠️ The recipient's email is temporarily not accepting messages.")
    except BadHeaderError:
        print("⚠️ Invalid header found.")
    except Exception as e:
        print(f"⚠️ Unexpected email sending error: {e}")



