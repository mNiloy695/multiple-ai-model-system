import requests
import json
import time
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords
User=get_user_model()


# CREDIT_DIDUCTION={
#     "flux-schnell":50,
#     "flux-dev-ultra-fast":70,
#     "flux-schnell-lora":70,
#     "flux-dev-lora-ultra-fast":75,
#     "flux-dev-lora":150,
#     "chroma":150
# }
# Fixed wavespeed_ai_call
def wavespeed_ai_call(model_id, api_key, payload=None, poll_interval=0.5, user_id=None, base_cost=500):
    
    if payload is None:
        payload = {
            "prompt": "A futuristic city skyline at sunset",
            "strength": 0.8,
            "size": "1024*1024",
            "num_inference_steps": 28,
            "seed": -1,
            "guidance_scale": 3.5,
            "num_images": 1,
            "output_format": "jpeg",
            "enable_base64_output": False,
            "enable_sync_mode": False
        }

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User Id not Found"}

    credit_account = CreditAccount.objects.filter(user=user).first()
    if not credit_account:
        credit_account = CreditAccount.objects.create(user=user, credits=0)

    num_images = payload.get('num_images', 1)
    image_deduct_credit = base_cost * num_images

    if credit_account.credits < image_deduct_credit:
        return {"error": "Insufficient credits! TOP UP NOW!"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    url = f"https://api.wavespeed.ai/api/v3/{model_id}"

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Error submitting {model_id}: {str(e)}"}

    request_id = response.json().get("data", {}).get("id")
    if not request_id:
        return {"error": f"No request ID returned for {model_id}"}

    result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    start_time = time.time()

    while True:
        try:
            resp = requests.get(result_url, headers={"Authorization": f"Bearer {api_key}"})
            resp.raise_for_status()
        except requests.RequestException as e:
            return {"error": f"Error checking status: {str(e)}"}

        result = resp.json().get("data", {})
        status = result.get("status")

        if status == "completed":
            credit_account.credits -= image_deduct_credit
            credit_account.save()
            user.total_token_used += image_deduct_credit
            user.save()
            trackUsedWords(user_id=user_id, words=image_deduct_credit)

            output_url = result.get("outputs", [None])[0]
            elapsed = time.time() - start_time
            return {
                "text": f"Image generated successfully ({payload.get('size')}) in {elapsed:.2f} seconds.",
                "images": [output_url] if output_url else []
            }

        elif status == "failed":
            return {"error": result.get("error", f"{model_id} generation failed")}

        time.sleep(poll_interval)

# Example usage:

# api_key = "YOUR_DYNAMIC_API_KEY_HERE"

# models = [
#     "flux-schnell",
#     "flux-dev-ultra-fast",
#     "flux-schnell-lora",
#     "flux-dev-lora-ultra-fast",
#     "flux-dev-lora",
#     "chroma"
# ]

# for model in models:
#     result = wavespeed_ai_call(model, api_key)
#     print(result)
