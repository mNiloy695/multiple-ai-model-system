# from plan.models import SubscriptionModel
from django.contrib.auth import get_user_model
from django.db.models import F
User=get_user_model()

def trackUsedWords(user_id,words):
    try:
        user=User.objects.get(id=user_id)
        print("debug >> user found:",user.total_token_used)
    except User.DoesNotExist:
        return "User Id not Found"
    # subscription=SubscriptionModel.objects.filter(user=user,status="active").first()
    # if subscription:
    #     unused_word=subscription.credits_words-subscription.used_words #2
    #     if words<=unused_word:
    #         subscription.used_words+=words
    #         subscription.save()
    #         print("Used words updated within subscription limit.")
    #     else:
    #         if unused_word>0:
    #             subscription.used_words+=unused_word
    #             subscription.save()
    #             print("2nd Used words updated to max subscription limit.")
    # else:
    #     return f'No active subscription found for user {user.email}'
    
    # User.objects.filter(id=user_id).update(
    #     total_token_used=F('total_token_used') + words
    # )
    # user.refresh_from_db()
    # print("The previous token_used is ............",user.total_token_used)
  
   
    # print("the updated token_used is ..............",user.total_token_used)

    return f"updated the used word"

