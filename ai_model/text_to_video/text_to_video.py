import requests
import json
import asyncio
import time
from asgiref.sync import sync_to_async
from ..track_used_word_subscription import trackUsedWords
from accounts.models import CreditAccount
import math

# base cost means cost for 1 second
data_of_models = {
    "openai/sora-2/text-to-video": {
        "size_options": ["720*1280", "1280*720"],
        "duration_options": [4, 8, 12]
    },
    "alibaba/wan-2.5/text-to-video": {
        "size_options": ["720*1280", "1280*720", "832*480", "480*832", "1920*1080", "1080*1920"],
        "duration_options": [5, 10]
    },
    "alibaba/wan-2.5/text-to-video-fast": {
        "size_options": ["720*1280", "1280*720", "832*480", "480*832", "1920*1080", "1080*1920"],
        "duration_options": [5, 10]
    },
    "google/veo3": {
        "size_options": ["16:9", "9:16"],
        "duration_options": [4, 6, 8],
        "resolution": ["720p", "1080p"]
    },
    "google/veo3-fast": {
        "size_options": ["16:9", "9:16"],
        "duration_options": [4, 6, 8],
        "resolution": ["720p", "1080p"]
    },
    "google/veo2": {
        "size_options": ["16:9", "9:16"],
        "duration_options": [5, 6, 7, 8],
        "resolution": ["720p"]
    },
    "lightricks/ltx-2-fast/text-to-video": {
        "duration_options": [6, 8, 10, 12, 14, 16, 18, 20]
    }
}

from django.contrib.auth import get_user_model
from django.db import transaction
User = get_user_model()

async def text_to_video_generation(model_id, prompt, api_key, duration, height, width, seed=-1, resolution="1080p", generate_audio=False, base_cost=500, user_id=None):
    API_KEY = api_key
    submit_url = f"https://api.wavespeed.ai/api/v3/{model_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    try:
        user = await sync_to_async(lambda: User.objects.select_related('creditaccount').get(id=user_id))()
    except User.DoesNotExist:
        raise ValueError("Invalid user account ID")
    
    total_base_cost = base_cost * duration

    try:
        user_account = await sync_to_async(lambda: user.creditaccount)()
        if user_account.credits < total_base_cost:
            raise ValueError("Insufficient credits to perform this operation.")
    except CreditAccount.DoesNotExist:
        raise ValueError("Invalid user ID")
    
    if model_id not in data_of_models:
        raise ValueError(f"Model ID {model_id} not supported.")
    
    payload = {}
    if model_id == "openai/sora-2/text-to-video":
        accourate_data = data_of_models[model_id]
        if not height and not width: width, height = 1280, 720
        if f"{width}*{height}" not in accourate_data["size_options"]: height, width = 1280, 720
        if duration not in accourate_data["duration_options"]: raise ValueError("Invalid duration")
        payload = {"duration": duration, "enable_prompt_expansion": False, "prompt": prompt, "seed": seed, "size": f"{width}*{height}"}

    elif model_id in ["alibaba/wan-2.5/text-to-video", "alibaba/wan-2.5/text-to-video-fast"]:
        accourate_data = data_of_models["alibaba/wan-2.5/text-to-video"]
        if not height and not width: width, height = 1280, 720
        if f"{width}*{height}" not in accourate_data["size_options"]: width, height = 1280, 720
        if duration not in accourate_data["duration_options"]: raise ValueError("Invalid duration")
        payload = {"duration": duration, "enable_prompt_expansion": False, "prompt": prompt, "seed": seed, "size": f"{width}*{height}"}

    elif model_id in ["google/veo3", "google/veo3-fast", "google/veo2"]:
        accourate_data = data_of_models["google/veo3"]
        if not height and not width: width, height = 16, 9
        aspect_ratio = f"{width}:{height}"
        if aspect_ratio not in accourate_data["size_options"]: aspect_ratio = "16:9"
        if duration not in accourate_data["duration_options"]: raise ValueError("Invalid duration")
        if resolution not in accourate_data["resolution"]: resolution = "720p"
        payload = {"duration": duration, "prompt": prompt, "generate_audio": generate_audio, "seed": seed, "aspect_ratio": aspect_ratio, "resolution": resolution}
    
    elif model_id == "lightricks/ltx-2-fast/text-to-video":
        accourate_data = data_of_models[model_id]
        if duration not in accourate_data["duration_options"]: raise ValueError("Invalid duration")
        payload = {"duration": duration, "prompt": prompt, "generate_audio": generate_audio}

    begin = time.time()
    
    # Submit task (Sync request in thread)
    response = await sync_to_async(requests.post)(submit_url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        raise Exception(f"Submit failed {response.status_code}: {response.text}")

    request_id = response.json()["data"]["id"]
    result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    
    # Polling result (Non-blocking)
    while True:
        poll_resp = await sync_to_async(requests.get)(result_url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=20)
        if poll_resp.status_code != 200:
            raise Exception(f"Polling error {poll_resp.status_code}")

        data = poll_resp.json()["data"]
        status = data["status"]

        if status == "completed":
            break
        if status == "failed":
            raise Exception(data.get("error", "Video generation failed"))
        
        await asyncio.sleep(2) # RELEASE THREAD during polling

    # Deduct credits atomically
    def _final_deduct():
        with transaction.atomic():
            acc = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
            if not acc:
                print(f"DEBUG: [VideoGen] Credit account NOT FOUND for user_id {user_id}")
                return
            
            print(f"DEBUG: [VideoGen] Pre-deduction. User: {user_id}, Current: {acc.credits}, Charging: {total_base_cost}")
            from decimal import Decimal
            acc.credits -= Decimal(str(total_base_cost))
            if acc.credits < 0:
                acc.credits = 0
            acc.save(update_fields=['credits'])
            
            u = User.objects.get(id=user_id)
            u.total_token_used += Decimal(str(total_base_cost))
            u.save(update_fields=['total_token_used'])
            
            # Video models don't track words against subscription
            # trackUsedWords(user_id, total_base_cost)
            print(f"DEBUG: [VideoGen] Deduction SUCCESS. New Balance: {acc.credits}")
    
    await sync_to_async(_final_deduct)()
    return data["outputs"][0]
