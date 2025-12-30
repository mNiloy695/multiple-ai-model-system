from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RewardsHistory
@receiver(post_save,sender=RewardsHistory)

def add_api_limit_on_reward_creation_time(sender,instance,created,**kwargs):
    if created:
        user=instance.user
        user.api_limit+=1
        user.save() 