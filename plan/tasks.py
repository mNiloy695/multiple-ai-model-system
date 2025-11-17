from celery import shared_task
from django.utils import timezone
from accounts.models import CreditAccount
from .models import SubscriptionModel
import logging

logger = logging.getLogger(__name__)
@shared_task
def update_expired_subscriptions():
    now = timezone.now()
    print("i am inner the updte expired subscription")
    # Get all active subscriptions that have expired
    expired_subs = SubscriptionModel.objects.filter(expire_date__lt=now, status="active")
    print("here the exp subs",expired_subs)
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
            logger.info(f"Updated subscription {sub.id} for user {sub.user.id}")
