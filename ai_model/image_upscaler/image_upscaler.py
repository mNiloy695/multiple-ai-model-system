# wavespeed-ai/image-upscaler


import os
import requests
import json
import time

from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from django.db import transaction
from ..track_used_word_subscription import trackUsedWords
User=get_user_model()


def  image_upscaler_wavespeed_ai(model_id,api_key,user_id,base_cost,image_url,target_resolution):
    print("Hello from WaveSpeedAI!")
    API_KEY = api_key

    # try:
    #     user=User.objects.get(id=user_id)
    # except User.DoesNotExist:
    #     return {"error":"User Id not Found"}
    
    # try:
    #     user_account=user.creditaccount
    #     if user_account.credits<base_cost:
    #         raise ValueError("Insufficient credits to perform this operation.")
    # except CreditAccount.DoesNotExist:
    #     return {"error":"Invalid user ID"}


    url = f"https://api.wavespeed.ai/api/v3/{model_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    possible_resolutions = ["2k", "4k", "8k"]
    if target_resolution not in possible_resolutions:
        raise ValueError(f"Invalid target resolution {target_resolution}. Available options: {possible_resolutions}")
    
    payload = {
        "enable_base64_output": False,
        "enable_sync_mode": False,
        "image": image_url,
        "output_format": "jpeg",
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
                    
                    # user.total_token_used+=int(base_cost)
                    print("The total token used after addition is........ ",user.total_token_used)
                    # print("the user is " ,user)
                    # user.save(update_fields=['total_token_used'])
                    from django.db.models import F
                    User.objects.filter(id=user_id).update( total_token_used=F("total_token_used") + int(base_cost)
)
                    print("the updated token_used is ..............",user.total_token_used)
                    user_account.save(update_fields=['credits'])
                    print("base_cost",base_cost)
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

        time.sleep(0.1)

