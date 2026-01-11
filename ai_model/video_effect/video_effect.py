
import os
import requests
import json
import time
from .payload import payload_data
from django.contrib.auth import get_user_model
User=get_user_model()
from accounts.models import CreditAccount

def video_effect(model_id,api_key,user_id,images,base_cost,duration=None,effect=None,resolution=None):
    print("Hello from WaveSpeedAI!")
    API_KEY = api_key
    payload=payload_data(model_id=model_id,duration=duration,effect=effect,image=images,resolution=resolution)
    print("payload ",payload)
    if payload is None:
        return {"error":"Invalid model ID"}
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

        time.sleep(0.5)

