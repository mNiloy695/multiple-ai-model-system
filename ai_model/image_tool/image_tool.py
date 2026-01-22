
import os
import requests
import json
import time
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
User=get_user_model()
from django.db import transaction
from ..track_used_word_subscription import trackUsedWords



# models_data={
#     "wavespeed-ai/image-text-remover":{
        
#     }
# }

import base64
from django.conf import settings

def get_image_as_base64(url):
    """
    Converts an image URL (local or remote) to a base64 data URI.
    """
    if not url:
        return None
    if url.startswith("data:"):
        return url
        
    try:
        # If it's a local URL (contains BASE_URL or local IP), try to read from disk if possible
        if (settings.BASE_URL and settings.BASE_URL in url) or "10.10.13.75" in url or "localhost" in url:
            # Extract relative path
            media_url = settings.MEDIA_URL
            if media_url in url:
                relative_path = url.split(media_url)[-1]
                local_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                        # Guess mime type from extension
                        ext = os.path.splitext(local_path)[1].lower()
                        mime = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
                        return f"data:{mime};base64,{encoded}"

        # Otherwise try to download it
        if url.startswith("http"):
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                encoded = base64.b64encode(resp.content).decode("utf-8")
                mime = resp.headers.get("Content-Type", "image/png")
                return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print(f"DEBUG: get_image_as_base64 failed: {e}")
        
    return url

def image_tool_via_wavespeedai(image_url, prompt,api_key,model_id,base_cost,user_id,style,target_language,target_resolution):

    print("Hello from WaveSpeedAI!")
    API_KEY=api_key
    
    url = f"https://api.wavespeed.ai/api/v3/{model_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    if not image_url:
        return {"error":"Image URL is required for image tool."}
    try:
        user=User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error":"User Id not Found"}
    
    try:
        user_account=user.creditaccount
        if user_account.credits<base_cost:
            raise ValueError("Insufficient credits to perform this operation.")
    except CreditAccount.DoesNotExist:
        return {"error":"Invalid user ID"}
    



  
    
    # Convert image to base64 to avoid external API connection issues with local URLs
    processed_image = get_image_as_base64(image_url)
    
    if model_id=="wavespeed-ai/image-text-remover":
        payload={
            "image":processed_image,
            "enable_sync_mode":False,
            "enable_base64_output":False
        }
    elif model_id=="bria/generate-background":
         payload = {
        "image": processed_image,
        "prompt": prompt,
        "enable_sync_mode": False,
        "enable_base64_output": False
    }
    elif model_id=="wavespeed-ai/prompt-optimizer":
        payload={
            "enable_sync_mode": False,
            "image": processed_image,
            "mode": "video",
            "style": style if style else "cinematic",
            "text": prompt
        }
        # print("the style is",payload["style"])

    elif model_id=="wavespeed-ai/image-translator":
        payload = {
        "enable_base64_output": False,
        "enable_sync_mode": False,
        "image": processed_image,
        "output_format": "jpeg",
        "target_language": target_language if target_language else "english"
    }
    
    elif model_id=="wavespeed-ai/image-background-remover":
        payload={
            "image":processed_image,
            "enable_sync_mode":False,
            "enable_base64_output":False
        }
    elif model_id=="wavespeed-ai/image-watermark-remover":
        payload={
            "image":processed_image,
            "enable_sync_mode":False,
            "enable_base64_output":False,
            "output_format": "jpeg"
        }
    elif model_id=="wavespeed-ai/image-upscaler":
        possible_resolutions = ["2k", "4k", "8k"]
        if target_resolution not in possible_resolutions:
          raise ValueError(f"Invalid target resolution {target_resolution}. Available options: {possible_resolutions}")
        payload = {
        "enable_base64_output": False,
        "enable_sync_mode": False,
        "image": processed_image,
        "output_format": "jpeg",
        "target_resolution": target_resolution if target_resolution else "4k"
    }
    else:
        raise ValueError(f"Model ID {model_id} not supported.")


 

    begin = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    print("image of image tool",image_url)
  
    if response.status_code == 200:
        result = response.json()["data"]
        request_id = result["id"]
        print(f"Task submitted successfully. Request ID: {request_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")

        raise Exception(f"Submit failed {response.status_code}: {response.text}")

    url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"

    headers = {"Authorization": f"Bearer {API_KEY}"}

#5ae107969768454dbb1d7e7d32a5051e

    # Poll for results
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()["data"]
            status = result["status"]

            if status == "completed":
                end = time.time()
                print(f"Task completed in {end - begin} seconds.")
                data = result["outputs"][0]
                with transaction.atomic():
                    user_account.credits-=int(base_cost)
                    user.total_token_used+=int(base_cost)
                    user.save(update_fields=['total_token_used'])
                    user_account.save(update_fields=['credits'])
                trackUsedWords(user_id,base_cost)
                return data

            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            # print(f"Error: {response.status_code}, {response.text}")
            break

        # time.sleep(0.1)
    


