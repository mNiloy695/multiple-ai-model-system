from plan.models import SubscriptionModel
from django.contrib.auth import get_user_model

User=get_user_model()

def trackUsedWords(user_id,words):
    user=User.objects.get(id=user_id)
    subscription=SubscriptionModel.objects.filter(user=user,status="active").first()
    if subscription:
        unused_word=subscription.credits_words-subscription.used_words
        if words<=unused_word:
            subscription.used_words+=words
            subscription.save()
    return f"updated the used word"

