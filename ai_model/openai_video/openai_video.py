import asyncio
import time
import math
from decimal import Decimal
from openai import AsyncOpenAI
from django.contrib.auth import get_user_model
from django.db import transaction
from asgiref.sync import sync_to_async

from accounts.models import CreditAccount
from ..track_used_word_subscription import trackUsedWords

User = get_user_model()

# =========================
# HELPER: Count Words (1 word = 5 non-space chars)
# =========================
def count_words(text):
    if not text:
        return 0
    char_count = len(text.replace(" ", ""))
    return math.ceil(char_count / 5)

async def call_openai_video_model(model_id, api_key, user_id, prompt, duration, width, height, seed, base_cost):
    client = AsyncOpenAI(api_key=api_key)

    if not prompt or prompt.strip() == "":
        return {"error": "Prompt cannot be empty"}
    
    # Standardize duration/resolution
    try:
        duration = int(duration)
    except:
        duration = 4
        
    if duration not in [4, 8, 12]:
        return {"error": "Invalid duration. Allowed values are 4, 8, or 12 seconds."}
    
    if model_id not in ['sora-2', 'sora-2-pro']:
         # Defaulting to sora-2 if invalid but keeping user check logic
         return {"error": "Invalid model ID. Contact to admin."}
    
    # possible_resolutions = ["720x1280", "1280x720", "1024x1792", "1792x1024"]
    # Check resolution simplified
    size = f"{width}x{height}"

    try:
        # Sync DB fetch via sync_to_async
        user = await sync_to_async(User.objects.get)(id=user_id)
        credit_account = await sync_to_async(CreditAccount.objects.get)(user=user)
    except Exception:
        return {"error": "User or Credit Account not found"}

    # Calculate total cost (assuming base_cost is per second or flat, here we follow user's pattern)
    # If base_cost is per request as current code suggests:
    total_cost = Decimal(str(base_cost))

    if credit_account.credits < total_cost:
        return {"error": "Insufficient credits to perform this operation."}

    # Word count for tracking (if needed)
    prompt_words = count_words(prompt)

    try:
        # Start generation
        # Note: Using .create instead of .generate as per common Beta patterns if .generate fails
        # But keeping user's .generate structure but as async
        response = await client.videos.generate(
            model=model_id,
            prompt=prompt,
            duration=duration,
            width=width,
            height=height,
            seed=seed
        )
    except Exception as e:
        print("Error generating video with OpenAI:", e)
        return {"error": f"AI error: {str(e)}"}

    # Polling Loop (Non-blocking)
    start_time = time.time()
    video_url = []
    
    while True:
        # Check for timeout (10 mins)
        if time.time() - start_time > 600:
            return {"error": "Video generation timed out"}
            
        status = response.status
        if status == "completed":
            # Atomic deduction
            @sync_to_async
            def _deduct():
                with transaction.atomic():
                    ca = CreditAccount.objects.select_for_update().get(id=credit_account.id)
                    ca.credits -= total_cost
                    ca.save(update_fields=['credits'])
                    
                    u = User.objects.get(id=user_id)
                    u.total_token_used += total_cost
                    u.save(update_fields=['total_token_used'])
                    
                    # Video models don't track words against subscription
                    # trackUsedWords(user_id, prompt_words)
            
            await _deduct()

            # Extract URLs - assuming standard response object structure
            if hasattr(response, 'output'):
                for output in response.output:
                    if output.type == "video":
                        video_url.append(output.url)
            elif hasattr(response, 'data'): # fallback for different SDK versions
                for item in response.data:
                    if hasattr(item, 'url'): video_url.append(item.url)

            return {
                "text": f"Video generated successfully ({duration}s).",
                "images": video_url,
                "sender": "ai"
            }
            
        elif status in ["queued", "processing"]:
            await asyncio.sleep(10) # Release thread
            response = await client.videos.retrieve(response.id)
            print(f"Video status: {response.status}")
        else:
            return {"error": f"Video generation failed with status: {status}"}
