from celery import shared_task
from django.utils import timezone
from accounts.models import CreditAccount
from .models import SubscriptionModel

@shared_task
def update_expired_subscriptions():
    now = timezone.now()
    # Get all active subscriptions that have expired
    expired_subs = SubscriptionModel.objects.filter(expire_date__lt=now, status="active")

    for sub in expired_subs:
        # Mark subscription as expired
        sub.status = 'expired'
        sub.save()

        # Calculate unused credits
        unused_credits = sub.credits_words - sub.used_words
        if unused_credits > 0:
            account = CreditAccount.objects.get(user=sub.user)
            account.credits -= unused_credits  # Add unused credits back
            account.save()
