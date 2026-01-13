
import os
import requests
import json
import time
from .payload import payload_data
from django.contrib.auth import get_user_model
import math
User=get_user_model()
from accounts.models import CreditAccount

def video_effect(model_id,api_key,user_id,images,base_cost,duration=None,effect=None,resolution=None,bgm=False,template=None,seed=0,sound_effect_switch=False):
    print("Hello from WaveSpeedAI!")
    API_KEY = api_key
    payload=payload_data(model_id=model_id,duration=duration,effect=effect,image=images,resolution=resolution,bgm=bgm,template=template,seed=seed,sound_effect_switch=sound_effect_switch)
    print("payload ",payload)
    if payload is None:
        raise Exception('Model id is wrong this model not allowed')
    try:
        user=User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error":"User Id not Found"}
    

    if model_id=="vidu/template/halloween":
        x_list=["pumpkin_head","tim_burton","broomstick_fly","sexy_devil","dance_with_ghost","crow_arrival","clown_makeup"]
        x_list_5x=["not_look_back_video","hadow_of_terror_video"]

        if template in x_list:
            base_cost=int(base_cost)*2

        elif template=="witchy_pet":
            base_cost=int(base_cost)*3
        
        elif template in x_list_5x:
            base_cost=math.ceil(float(base_cost)*2.5)

    if model_id == "video-effects/dust-me-away" or model_id=="video-effects/red-or-white":
            resolution_allowed = ["540p", "360p", "720p"]

            if resolution not in resolution_allowed:
             resolution = "540p"
    else:
        if resolution == "720p":
            base_cost = math.ceil(float(base_cost) * 1.4)


    if model_id=="pixverse/pixverse-v5-effects":
        resolution_allowed=["540p", "360p", "720p","1080p"]

        if resolution not in resolution_allowed:
            resolution="540p"

        # if (resolution=="540p" and duration==8) or (resolution=="360p" and duration==8):
        #     base_cost=math.ceil(float(base_cost)*2)
        
        # elif resolution=="720p" and duration==5:
        #         base_cost=math.ceil(float(base_cost)*1.33)

        # elif (resolution=="720p" and duration==8 ) or (resolution=="1080p" and duration==5):
        #         base_cost=math.ceil(float(base_cost)*2.67)
            
        # elif (resolution=="1080p" and duration==8):
        #         base_cost=math.ceil(float(base_cost)*5.33)
        multipliers = {("360p", 8): 2,("540p", 8): 2,("720p", 5): 1.33, ("720p", 8): 2.67,("1080p", 5): 2.67,("1080p", 8): 5.33,}
        key = (resolution, duration)
        if key in multipliers:
            base_cost = math.ceil(float(base_cost) * multipliers[key])
        print(base_cost,"--------------------------")


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

