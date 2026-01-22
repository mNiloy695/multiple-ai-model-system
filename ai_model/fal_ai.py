import os
import fal_client
from .track_used_word_subscription import trackUsedWords
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
User = get_user_model()

# call_fal_ai(api_key, prompt,model,user_id,base_cost=None,seed=6252023, steps=50, cfg_scale=7.0, size="512x512"):
def call_fal_ai(api_key, prompt,model,user_id,num_images=1,base_cost=None,seed=6252023, steps=50, cfg_scale=7.0, size="512x512"):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User Id not Found"}
    
    credit_account = CreditAccount.objects.filter(user=user).first()
    if not credit_account:
        credit_account = CreditAccount.objects.create(user=user, credits=0)
    

    image_deduct_credit = base_cost*num_images if base_cost else 500


    if credit_account.credits <image_deduct_credit:
        return {"error": "Insufficient credits! TOP UP NOW!"}
    
    credit_account.credits -= image_deduct_credit
    if credit_account.credits < 0:
        credit_account.credits = 0
    credit_account.save()
    trackUsedWords(user, word_count=image_deduct_credit)
    user.total_token_used+=image_deduct_credit
    user.save()


    try:
        # Set the API key dynamically for this session
        
        os.environ["FAL_KEY"] = api_key

        # Submit the request
        handler = fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "seed": seed,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "size": size
            }
        )

        result = handler.get()

        # Extract image URL
        images = result.get("images", [])
        # image_url = images[0].get("url") if images else None
        image_url = [img.get("url") for img in images if img]


        return {
            "text": "Image generated successfully.",
            "images": image_url
        }

    except Exception as e:
        credit_account.credits+=image_deduct_credit
        credit_account.save()
        user.total_token_used-=image_deduct_credit
        user.save()
        error_str = str(e)
        if "key" in error_str.lower():
            return {"error": "Authentication failed: Invalid API key."}
        return {"error": "Error generating image. Please try again later."}
