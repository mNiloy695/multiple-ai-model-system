import os
import requests
import json
import time

from django.contrib.auth import get_user_model
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

def image_to_3d(model_id,api_key,user_id,images,base_cost):


    print("Hello from WaveSpeedAI!")

    if model_id !="tripo3d/v2.5/image-to-3d":
        return {"error":"This model is not allow"}
    
    try:
        user=User.objects.select_related("creditaccount").get(id=user_id)

    except User.DoesNotExist:
        return {"error":"User not found"}
    
    try:
        user_account=user.creditaccount
        if user_account.credits<base_cost:
            raise ValueError("Insufficient credits to perform this operation.")
    except CreditAccount.DoesNotExist:
        return {"error":"Invalid user ID"}
    
    
    API_KEY = api_key
    url = f"https://api.wavespeed.ai/api/v3/{model_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    processed_image = get_image_as_base64(images)
    payload = {
        "image": processed_image
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

    

    # Poll for results
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()["data"]
            status = result["status"]

            if status == "completed":
                end = time.time()
                print(f"Task completed in {end - begin} seconds.")
                url = result["outputs"][0]
                print(f"Task completed. URL: {url}")
                user_account.credits-=int(base_cost)
                user.total_token_used+=int(base_cost)
                user_account.save()
                user.save()
                return url
            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break


