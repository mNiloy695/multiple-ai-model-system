
import os
import requests
import json
import time

from django.contrib.auth import get_user_model
User=get_user_model()

from accounts.models import CreditAccount


ASPECT_RATIO=["1:1","3:2","2:3","3:4","4:3","4:5","5:4","9:16","16:9","21:9"]

def image_edit(model_id,prompt,api_key,user_id,output_format="png",aspect_ratio="1:1",base_cost=500,images=None):
    print("Hello from WaveSpeedAI!")
    API_KEY = api_key

    if aspect_ratio not in ASPECT_RATIO:
        return {"error":f"Invalid target aspect_ratio {aspect_ratio}. Available options: {ASPECT_RATIO}"}
    
    if output_format not in ['png','jpeg']:
        return {"error":f"Invalid target output_format.Available options: 'png or jpeg"}
    
    if model_id!="google/nano-banana/edit":
        return {"error":f"Invalid model Id .Available model is google/nano-banana/edit"}
    
    if not user_id:
        return {"error":"User id not found It's required"}
    

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
    


    
    payload = {
        "prompt": prompt,
        "enable_base64_output": False,
        "enable_sync_mode": False,
        "aspect_ratio":aspect_ratio,
        "images": images if isinstance(images,list) else [],
        "output_format": output_format
    }
    

    


    


    url = f"https://api.wavespeed.ai/api/v3/{model_id}/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
  

    begin = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()["data"]
        request_id = result["id"]
        print(f"Task submitted successfully. Request ID: {request_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return

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
                
                data = result["outputs"][0]
                print(f"Task completed. URL: {url}")

                user_account.credits-=int(base_cost)
                user.total_token_used+=int(base_cost)
                user_account.save()
                user.save()

                return data
            
            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        time.sleep(0.1)

