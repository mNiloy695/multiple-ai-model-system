from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import CreditAccount,CreditTransaction,UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_credit_account(sender, instance, created, **kwargs):
    if instance.is_active:
        if not hasattr(instance, 'creditaccount'):
            CreditAccount.objects.create(user=instance, credits=1000)
            CreditTransaction.objects.create(
                credit_account=instance.creditaccount,
                amount=1000,
                transaction_type='bonus',
                message='Initial bonus credits for account activation'
            )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance,first_name=instance.first_name,last_name=instance.last_name)