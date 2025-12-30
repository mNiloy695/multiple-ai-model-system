# from django.db.models.signals import post_save
# from django.dispatch import receiver
# # from .models import SubscriptionModel

# @receiver(post_save, sender=SubscriptionModel)
# def user_api_limitation_add(sender,instance,created,**kwargs):
#     if created:
#         user=instance.user
#         user.api_limit=5000
#         user.word_limit=instance.credits_words
#         user.save()

