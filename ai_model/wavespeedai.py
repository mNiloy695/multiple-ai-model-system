import requests
import json
import time
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from track_used_word_subscription import trackUsedWords
User=get_user_model()


CREDIT_DIDUCTION={
    "flux-schnell":50,
    "flux-dev-ultra-fast":70,
    "flux-schnell-lora":70,
    "flux-dev-lora-ultra-fast":75,
    "flux-dev-lora":150,
    "chroma":150
}
def wavespeed_ai_call(model_id, api_key, payload=None, poll_interval=0.5,user_id=None):
    """
    Dynamic WaveSpeedAI API caller.

    Args:
        model_id (str): Model name, e.g., "flux-dev-ultra-fast"
        api_key (str): Your WaveSpeedAI API key
        payload (dict, optional): API request payload. Uses default if None.
        poll_interval (float): Seconds to wait between status checks
    Returns:
        str: Output URL or error message
    """
    if payload is None:
        payload = {
            "prompt":"A futuristic city skyline at sunset",
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
        user=User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error":"User Id not Found"}
    
    credit_account=CreditAccount.objects.filter(user=user).first()

    if not credit_account:
        return {"error":"The user not have any account"}
    
    image_deduct_credit=CREDIT_DIDUCTION.get(model_id)*payload.get('num_images')
    
    credits=credit_account.credits
    if credits<image_deduct_credit:
        return {"error":"Insufficient credits ! TOP UP NOW !"}

    # Default payload if none provided
 
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    url = f"https://api.wavespeed.ai/api/v3/wavespeed-ai/{model_id}"

    # Submit the task
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        return f"Error submitting {model_id}: {response.status_code}, {response.text}"

    request_id = response.json()["data"]["id"]
    print(f"Task submitted for {model_id}. Request ID: {request_id}")

    # Poll for result
    result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    start_time = time.time()
    while True:
        resp = requests.get(result_url, headers={"Authorization": f"Bearer {api_key}"})
        if resp.status_code != 200:
            return f"Error checking status: {resp.status_code}, {resp.text}"

        result = resp.json()["data"]
        status = result["status"]

        if status == "completed":
            credit_account.credits-=image_deduct_credit
            credit_account.save()
            user.total_token_used+=image_deduct_credit
            trackUsedWords(user_id=user_id,words=image_deduct_credit)
            output_url = result["outputs"][0]
            elapsed = time.time() - start_time
            # return f"{model_id} completed in {elapsed:.2f}s. Output URL: {output_url}"
            return {
            "text": f"Image generated successfully ({payload.get('size')}) using {model_id}.",
            "images": [output_url]
        }
        elif status == "failed":
            return f"{model_id} failed: {result.get('error')}"

        print(f"{model_id} still processing...")
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
