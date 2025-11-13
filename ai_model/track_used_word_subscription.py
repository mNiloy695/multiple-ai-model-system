from plan.models import SubscriptionModel
from django.contrib.auth import get_user_model

User=get_user_model()

def trackUsedWords(user_id,words):
    user=User.objects.get(id=user_id)
    subscription=SubscriptionModel.objects.filter(user=user,status="active").first()
    if subscription:
        unused_word=subscription.credits_words-subscription.used_words #2
        if words<=unused_word:
            subscription.used_words+=words
            subscription.save()
        else:
            if unused_word>0:
                subscription.used_words+=unused_word
                subscription.save()
    return f"updated the used word"

