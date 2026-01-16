import requests
import json
import time
from ..track_used_word_subscription import trackUsedWords
from accounts.models import CreditAccount
#base cost means cost for 1 second
data_of_models={
    "openai/sora-2/text-to-video":{
        "size_options":["720*1280","1280*720"],
        "duration_options":[4,8,12]
    },
    "alibaba/wan-2.5/text-to-video":{
        "size_options":["720*1280","1280*720","832*480","480*832","1920*1080","1080*1920"],
        "duration_options":[5,10]
    },
    "alibaba/wan-2.5/text-to-video-fast":{
        "size_options":["720*1280","1280*720","832*480","480*832","1920*1080","1080*1920"],
        "duration_options":[5,10]
    },
    "google/veo3":{
        "size_options":["16:9","9:16"],
        "duration_options":[4,6,8],
        "resolution":["720p","1080p"]
    },
    "google/veo3-fast":{
        "size_options":["16:9","9:16"],
        "duration_options":[4,6,8],
        "resolution":["720p","1080p"]
    },
    "google/veo2":{
        "size_options":["16:9","9:16"],
        "duration_options":[5,6,7,8],
        "resolution":["720p"]
    },
    "lightricks/ltx-2-fast/text-to-video":{
        "duration_options":[6,8,10,12,14,16,18,20]
    }
}

from django.contrib.auth import get_user_model
from django.db import transaction
User=get_user_model()


def text_to_video_generation(model_id, prompt, api_key, duration, height, width, seed=-1,resolution="1080p",generate_audio=False,base_cost=500,user_id=None):
    API_KEY = api_key
    submit_url = f"https://api.wavespeed.ai/api/v3/{model_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    print("user",user_id)
    try:
        user=User.objects.select_related('creditaccount').get(id=user_id)
        
    except User.DoesNotExist:
        raise ValueError("Invalid user account ID")
    
    #base cost means cost for 1 second
    
    total_base_cost=base_cost*duration

    try:
        user_account=user.creditaccount
        if user_account.credits<total_base_cost:
            raise ValueError("Insufficient credits to perform this operation.")
    except CreditAccount.DoesNotExist:
        raise ValueError("Invalid user ID")
    

    if model_id not in data_of_models:
        raise ValueError(f"Model ID {model_id} not supported.")
    

    
    
    #for sora-2/text-to-video
    
    if model_id=="openai/sora-2/text-to-video":
         accourate_data_for_model=data_of_models["openai/sora-2/text-to-video"]


         if not height and not width:
             width,height=1280,720

         if f"{width}*{height}" not in accourate_data_for_model["size_options"]:
            height,width=1280,720
         if duration not in accourate_data_for_model["duration_options"]:
            raise ValueError(f"Invalid duration {duration}. Available options: {accourate_data_for_model['duration_options']}")
         


         payload = {
        "duration": duration,
        "enable_prompt_expansion": False,
        "prompt": prompt,
        "seed": seed,
        "size": f"{width}*{height}",
       }
         
    
    #for alibaba wan-2.5/text-to-video

    elif model_id=="alibaba/wan-2.5/text-to-video" or model_id=="alibaba/wan-2.5/text-to-video-fast":

        accourate_data_for_model=data_of_models["alibaba/wan-2.5/text-to-video"] or data_of_models["alibaba/wan-2.5/text-to-video-fast"]
        if not height and not width:
                width,height=1280,720
        if f"{width}*{height}" not in accourate_data_for_model["size_options"]:
            width,height=1280,720
        if duration not in accourate_data_for_model["duration_options"]:
            raise ValueError(f"Invalid duration {duration}. Available options: {accourate_data_for_model['duration_options']}")

        payload = {
        "duration": duration,
        "enable_prompt_expansion": False,
        "prompt": prompt,
        "seed": seed,
        "size": f"{width}*{height}",
       }
        
    #for google veo3

    elif model_id=="google/veo3" or model_id=="google/veo3-fast" or model_id=="google/veo2":
        accourate_data_for_model=data_of_models["google/veo3"] or data_of_models["google/veo3-fast"] or data_of_models["google/veo2"]
        if not height and not width:
                width,height=16,9
        aspect_ratio = f"{width}:{height}"
        if aspect_ratio not in accourate_data_for_model["size_options"]:
            width,height=16,9
            aspect_ratio = f"{width}:{height}"

        if duration not in accourate_data_for_model["duration_options"]:
            raise ValueError(f"Invalid duration {duration}. Available options: {accourate_data_for_model['duration_options']}")

        if resolution not in accourate_data_for_model["resolution"]:
            resolution="720p"

        payload = {
        "duration": duration,
        "prompt": prompt,
        "generate_audio":generate_audio,
        "seed": seed,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution
       }
    
    elif model_id=="lightricks/ltx-2-fast/text-to-video":
        accourate_data_for_model=data_of_models["lightricks/ltx-2-fast/text-to-video"]

        if duration not in accourate_data_for_model["duration_options"]:
            raise ValueError(f"Invalid duration {duration}. Available options: {accourate_data_for_model['duration_options']}")
        
        payload = {
        "duration": duration,
        "prompt": prompt,
        "generate_audio":generate_audio,
       }
        

    begin = time.time()

    # 🔹 Submit task
    response = requests.post(submit_url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Submit failed {response.status_code}: {response.text}")

    result = response.json()["data"]
    request_id = result["id"]
    print("total_base_cost",total_base_cost)
    # 🔹 Poll result
    result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"

    headers = {"Authorization": f"Bearer {API_KEY}"}

    while True:
        response = requests.get(result_url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Polling error {response.status_code}: {response.text}")

        data = response.json()["data"]
        status = data["status"]

        if status == "completed":
            end = time.time()
            with transaction.atomic():
                user_account=CreditAccount.objects.select_for_update().get(user=user)
                user = User.objects.select_for_update().get(id=user_id)

                if user_account.credits<total_base_cost:
                    raise ValueError("Insufficient credits to perform this operation.")
                
                user_account.credits-=total_base_cost
            
                trackUsedWords(user.id,total_base_cost)
                user.total_token_used+=total_base_cost
                user.save(update_fields=['total_token_used'])
                user_account.save(update_fields=['credits'])
            print(f"Completed in {end - begin:.2f}s")
            return data["outputs"][0]
        
        if status =="processing":
            print("Processing...")
        if status == "failed":
            raise Exception(data.get("error", "Video generation failed"))

        # time.sleep(0.5)
