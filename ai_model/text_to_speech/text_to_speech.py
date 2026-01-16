
import os
import requests
import json
import time
from .voice_id import voice_id_check
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
User=get_user_model()

def text_to_sound(model_id,api_key,user_id,base_cost,bitrate=None,emotion="happy",english_normalization=True,formate="mp3",prompt="",language_boost="auto",pitch=1,sample_rate=None,speed=1,voice_id="Wise_Woman",volume=1,channel=None):
    print("Hello from WaveSpeedAI!")
    if not user_id:
        return {"error":"User id not found It's required"}
    
    if not prompt or not isinstance(prompt, str):
        return {"error": "Text prompt is required and must be a string"}
    try:
        user=User.objects.select_related("creditaccount").get(id=user_id)

    except User.DoesNotExist:
        return {"error":"User not found"}
    from decimal import Decimal
    prompts_cost = Decimal(len(prompt)) / Decimal("1000") if prompt else Decimal("0")
    base_cost = Decimal(str(base_cost))  # ensures safet
    prompts_cost = prompts_cost * base_cost


    
    try:
        user_account=user.creditaccount
        if user_account.credits<prompts_cost:
            raise ValueError("Insufficient credits to perform this operation.")
    except CreditAccount.DoesNotExist:
        return {"error":"Invalid user ID"}


    API_KEY = api_key
    url = f"https://api.wavespeed.ai/api/v3/{model_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    is_voice_id=voice_id_check(voice_id)
    if speed>2 or volume>2:
        speed=2
        volume=2
    if speed<=0.5:
        speed=0.5

    if volume<=0.1:
        volume=0.1
        
    
    if pitch>12:
        pitch=12
    if pitch<-12:
        pitch=-12
    

    emotion_list=["happy","sad","angry","fearful","disgusted","surprised","neutral"]

    if emotion not in emotion_list:
        emotion="happy"

    

    if english_normalization not in [True,False]:
        english_normalization=False

    
    sample_rate_list=[8000, 16000, 22050, 24000, 32000, 44100]

    if sample_rate not in sample_rate_list:
        sample_rate=8000

    bitrate_list=[32000, 64000, 128000, 256000]

    if bitrate not in bitrate_list:
        bitrate=32000

    channel_list=[1, 2]
    if channel not in channel_list:
        channel=1
    
    format_list=['mp3','wav','pcm','flac']

    if not formate in format_list:
        formate="mp3"
    
    languages = [
    "Chinese",
    "Chinese_Yue",
    "English",
    "Arabic",
    "Russian",
    "Spanish",
    "French",
    "Portuguese",
    "German",
    "Turkish",
    "Dutch",
    "Ukrainian",
    "Vietnamese",
    "Indonesian",
    "Japanese",
    "Italian",
    "Korean",
    "Thai",
    "Polish",
    "Romanian",
    "Greek",
    "Czech",
    "Finnish",
    "Hindi",
    "auto"
]
    if language_boost not in languages:
        language_boost="auto"

    payload = {
        "bitrate": bitrate,
        "emotion": emotion,
        "enable_sync_mode": False,
        "english_normalization": english_normalization,
        "format": formate,
        "language_boost":language_boost,
        "pitch":pitch,
        "sample_rate":sample_rate,
        "speed": speed,
        "text":prompt,
        "voice_id":voice_id if is_voice_id else "Wise_Woman",
        "volume": volume
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
                user_account.credits-=prompts_cost
                user_account.save()
                user.total_token_used+=prompts_cost
                user.save()
                print(f"Task completed. URL: {url}")

                
                return url
            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        # time.sleep(0.5)

