import os
import requests
import json
import time

from django.contrib.auth import get_user_model
User=get_user_model()
from accounts.models import CreditAccount

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
    url = "https://api.wavespeed.ai/api/v3/tripo3d/v2.5/image-to-3d"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "image": "https://d1q70pf5vjeyhc.cloudfront.net/media/fb8f674bbb1a429d947016fd223cfae1/images/1754460996352484824_klzOKHDA.png"
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


