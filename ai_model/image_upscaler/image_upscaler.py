# wavespeed-ai/image-upscaler


import os
import requests
import json
import time

from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from django.db import transaction
from ..track_used_word_subscription import trackUsedWords
import base64
from django.conf import settings

User=get_user_model()

def get_image_as_base64(url):
    """
    Converts an image URL (local or remote) to a base64 data URI.
    """
    if not url:
        return None
    if url.startswith("data:"):
        return url
        
    try:
        if (settings.BASE_URL and settings.BASE_URL in url) or "10.10.13.75" in url or "localhost" in url:
            media_url = settings.MEDIA_URL
            if media_url in url:
                relative_path = url.split(media_url)[-1]
                local_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                        ext = os.path.splitext(local_path)[1].lower()
                        mime = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
                        return f"data:{mime};base64,{encoded}"

        if url.startswith("http"):
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                encoded = base64.b64encode(resp.content).decode("utf-8")
                mime = resp.headers.get("Content-Type", "image/png")
                return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print(f"DEBUG: get_image_as_base64 failed: {e}")
    return url

def  image_upscaler_wavespeed_ai(model_id,api_key,user_id,base_cost,image_url,target_resolution):
    print("Hello from WaveSpeedAI!")
    API_KEY = api_key

    if model_id !="wavespeed-ai/flashvsr":
        # return {"error":'Image upscaler only support wavespeed-ai/flashvsr model'}
        raise ValueError("Image upscaler only support wavespeed-ai/flashvsr model")
    if target_resolution not in ['1080p','720p','2k','4k']:
        raise ValueError("The targeted resulation can be 1080p/720p/2k/4k")
    

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


    url = f"https://api.wavespeed.ai/api/v3/{model_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # possible_resolutions = ["2k", "4k", "8k"]
    # if target_resolution not in possible_resolutions:
    #     raise ValueError(f"Invalid target resolution {target_resolution}. Available options: {possible_resolutions}")
    
    processed_image = get_image_as_base64(image_url)
    payload = {
        "video": processed_image,
        "target_resolution": target_resolution if target_resolution else "4k"
    }

    begin = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()["data"]
        request_id = result["id"]
        print(f"Task submitted successfully. Request ID: {request_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
        raise Exception(f"Submit failed {response.status_code}: {response.text}")
    
    url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    if response.status_code != 200:
        raise Exception(f"Submit failed {response.status_code}: {response.text}")
    

    # Poll for results
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Polling error {response.status_code}: {response.text}")
        if response.status_code == 200:
            result = response.json()["data"]
            status = result["status"]

            if status == "completed":
                end = time.time()
                print(f"Task completed in {end - begin} seconds.")
                url = result["outputs"][0]
                print(f"Task completed. URL: {url}")

                with transaction.atomic():
                    try:
                        user=User.objects.select_for_update().get(id=user_id)
                        print("The previous token_used is ............",user.total_token_used)
                    except User.DoesNotExist:
                        raise ValueError("User Id not Found")
                    try: 
                        user_account=CreditAccount.objects.select_for_update().get(user__id=user_id)
                    except CreditAccount.DoesNotExist:
                        raise ValueError("Invalid user ID")
                                     
                    if user_account.credits<base_cost:
                        raise ValueError("Insufficient credits to perform this operation.")
                    
                    user_account.credits-=int(base_cost)
                    
                    user.total_token_used+=int(base_cost)
                    # print("the user is " ,user)
                    user.save(update_fields=['total_token_used'])
                    user_account.save(update_fields=['credits'])
                trackUsedWords(user_id,base_cost)
                return url
                
                
            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        # time.sleep(0.1)

