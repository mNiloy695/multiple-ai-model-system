import requests
import json
import asyncio
import time
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords
from asgiref.sync import sync_to_async
from django.db import transaction
from decimal import Decimal

User = get_user_model()

async def wavespeed_ai_call(model_id, api_key, payload=None, poll_interval=0.5, user_id=None, base_cost=500):
    if payload is None:
        payload = {
            "prompt": "A futuristic city skyline at sunset",
            "strength": 0.8,
            "size": "1024*1024",
            "num_inference_steps": 28,
            "seed": -1,
            "guidance_scale": 3.5,
            "num_images": 1,
            "output_format": "jpeg",
            "enable_base64_output": False,
            "enable_sync_mode": False
        }

    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
    except User.DoesNotExist:
        return {"error": "User Id not Found"}
    
    print("payload:", payload)
    credit_account = await sync_to_async(lambda: CreditAccount.objects.filter(user=user).first())()
    if not credit_account:
        credit_account = await sync_to_async(CreditAccount.objects.create)(user=user, credits=0)

    num_images = payload.get('num_images', 1)
    image_deduct_credit = base_cost * num_images

    if credit_account.credits < image_deduct_credit:
        return {"error": "Insufficient credits! TOP UP NOW!"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    url = f"https://api.wavespeed.ai/api/v3/{model_id}"

    try:
        # Run synchronous requests in a thread pool using sync_to_async
        response = await sync_to_async(requests.post, thread_sensitive=False)(url, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
    except Exception as e:
        error_str = str(e)
        if "api_key" in error_str.lower() or "authorization" in error_str.lower():
            return {"error": "Authentication failed: Invalid API key."}
        return {"error": f"Error submitting request. Please try again later."}

    request_id = response.json().get("data", {}).get("id")
    if not request_id:
        return {"error": "No request ID returned"}

    result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    start_time = time.time()

    status = "pending"
    result = {}
    
    while True:
        try:
            # Check for total timeout (10 minutes)
            if time.time() - start_time > 600:
                return {"error": "Request timed out after 10 minutes"}

            resp = await sync_to_async(requests.get, thread_sensitive=False)(result_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            return {"error": f"Error checking status: {str(e)}"}

        result = resp.json().get("data", {})
        status = result.get("status")
        
        if status not in ["completed", "failed"]:
            await asyncio.sleep(poll_interval)
        else:
            break

    if status == "completed":
        print(f"Task completed.")
        
        # Deduct credits atomically in a separate sync function
        def _process_credits():
            with transaction.atomic():
                ca = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
                if not ca:
                    print(f"DEBUG: Wavespeed Credit account NOT FOUND for user_id {user_id}")
                    return
                print(f"DEBUG: Wavespeed Pre-deduction. User: {user_id}, Current: {ca.credits}, Charging: {image_deduct_credit}")
                ca.credits -= Decimal(str(image_deduct_credit))
                if ca.credits < 0:
                    ca.credits = 0
                ca.save(update_fields=["credits"])
                
                u = User.objects.get(id=user_id)
                u.total_token_used += Decimal(str(image_deduct_credit))
                u.save(update_fields=["total_token_used"])
                print(f"DEBUG: Wavespeed Deduction SUCCESS. New Balance: {ca.credits}")
        
        await sync_to_async(_process_credits)()
        # Image models don't track words

        output_url = result.get("outputs", [None])[0]
        elapsed = time.time() - start_time
        return {
            "text": f"Image generated successfully ({payload.get('size')}) in {elapsed:.2f} seconds.",
            "images": [output_url] if output_url else []
        }

    elif status == "failed":
        print("Generation failed")
        return {"error": result.get("error", "Generation failed")}
    
    return {"error": "Unknown status"}
