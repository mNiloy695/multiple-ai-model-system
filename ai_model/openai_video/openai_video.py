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
import asyncio
from decimal import Decimal
from django.db import transaction
from asgiref.sync import sync_to_async
from openai import AsyncOpenAI
from .helpers import save_video  # Import the helper function

async def call_openai_video_model(
    model_id, api_key, user_id, prompt, duration, width, height, seed, base_cost
):
    client = AsyncOpenAI(api_key=api_key)

    

    
    if not prompt or prompt.strip() == "":
        return {"error": "Prompt cannot be empty"}
    
    try:
        duration = str(duration)
    except:
        duration = "4"
    
    if duration not in ["4", "8", "12"]:
        return {"error": "Invalid duration. Allowed values are 4, 8, or 12 second's."}
    
    if model_id not in ["sora-2", "sora-2-pro"]:
        return {"error": "Invalid model ID. Contact admin."}
    
    # Allow higher-resolution options for both models. Apply a multiplier for high-res to account
    # for greater compute cost. We choose a slightly lower multiplier for `sora-2` and a higher
    # multiplier for `sora-2-pro`.
    # possible_resolutions = ["720x1280", "1280x720", "1024x1792", "1792x1024"]
    if model_id == "sora-2-pro":
        possible_resolutions = ["720x1280", "1280x720", "1024x1792", "1792x1024"]
    else:
        possible_resolutions = ["720x1280", "1280x720"]

    # Validate requested resolution
    if f"{width}x{height}" not in possible_resolutions:
        return {"error": f"Invalid resolution. Allowed resolutions are: {', '.join(possible_resolutions)}"}

    # Determine if this is a high-resolution request
    high_res_sizes = {"1024x1792", "1792x1024"}
    requested_size = f"{width}x{height}"
    if requested_size in high_res_sizes:
        # Apply cost multipliers per model
        if model_id == "sora-2-pro":
            base_cost = math.ceil(base_cost * 1.67)
        else:
            # sora-2 (non-pro) gets a slightly smaller multiplier but still higher cost
            base_cost = math.ceil(base_cost)

    # if f"{width}x{height}" not in possible_resolutions:
    #     return {"error": f"Invalid resolution. Allowed resolutions are: {', '.join(possible_resolutions)}"}
   

    


    
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        credit_account = await sync_to_async(CreditAccount.objects.get)(user=user)
    except Exception:
        return {"error": "User or Credit Account not found"}
    
    total_cost = Decimal(str(base_cost)) * Decimal(duration)
    if credit_account.credits < total_cost:
        return {"error": "Insufficient credits to perform this operation."}
    
    # CREATE VIDEO JOB (returns job_id, not video URL)
    try:
        response = await client.videos.create(
            model=model_id,
            prompt=prompt,
            seconds=duration,  # string: "4", "8", or "12"
            size=f"{width}x{height}",
        )
    except Exception as e:
        print("Error generating video with OpenAI:", e)
        return {"error": f"AI error: {str(e)}"}
    
    # EXTRACT JOB ID from response
    job_id = None
    if hasattr(response, "id"):
        job_id = response.id
    elif isinstance(response, dict) and "id" in response:
        job_id = response["id"]
    
    if not job_id:
        print("DEBUG: No job ID found. Response:", response.__dict__ if hasattr(response, "__dict__") else response)
        return {"error": "Video job created but no job ID found in response."}
    
    print(f"Video job created: {job_id}")
    
    #  POLL FOR COMPLETION (with exponential backoff)
    max_wait = 600  # 10 minutes max
    elapsed = 0
    poll_interval = 5  # start at 5 seconds
    
    while elapsed < max_wait:
        try:
            status_response = await client.videos.retrieve(job_id)
        except Exception as e:
            print(f"Error retrieving video status: {e}")
            return {"error": f"Failed to check video status: {str(e)}"}
        
        status = getattr(status_response, "status", None)
        progress = getattr(status_response, "progress", 0)
        print(f"Video {job_id} status: {status} ({progress}%)")
        
        if status == "completed":
            print(f"Video completed, downloading...")
            
            # DOWNLOAD VIDEO CONTENT using /content endpoint
            try:
                video_content = await client.videos.download_content(job_id)
                video_content = video_content.read()
                
            except Exception as e:
                print(f"Error downloading video: {e}")
                return {"error": f"Failed to download video: {str(e)}"}
            
            #  SAVE VIDEO using helper function
            save_result = save_video(video_content)
            if not save_result["success"]:
                return {"error": save_result["error"]}
            
            video_filename = save_result["filename"]
            video_url = save_result["url"]
            
            #  Deduct credits ONLY after success
            @sync_to_async
            def _deduct():
                with transaction.atomic():
                    ca = CreditAccount.objects.select_for_update().get(id=credit_account.id)
                    ca.credits -= total_cost
                    ca.save(update_fields=["credits"])
                    u = User.objects.get(id=user_id)
                    u.total_token_used += total_cost
                    u.save(update_fields=["total_token_used"])
            
            try:
                await _deduct()
            except Exception as e:
                return {"error": f"Credit deduction failed: {str(e)}"}
            
            return {
                "text": f"Video generated successfully ({duration}s).",
                "videos": [video_url],  # Return accessible URL
                "images":[video_url],
                "filename": video_filename,
                "job_id": job_id,
                "sender": "ai",
            }
        
        elif status == "failed":
            print(f"Video generation failed.")
            error_msg = getattr(status_response, "error", "Unknown error")
            return {"error": f"Video generation failed: {error_msg}"}
        
        elif status in ["queued", "in_progress"]:
            # Still processing, wait and retry
            print(f"Video {job_id} still processing. Waiting {poll_interval}s before next check...")
            await asyncio.sleep(poll_interval)
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            poll_interval = min(poll_interval * 1.5, 30)  # exponential backoff up to 30s
        else:
            return {"error": f"Unknown job status: {status}"}
    
    return {"error": "Video generation timeout. Job took too long to complete."}
    
# =========================

# =========================
# HELPER: Count Words (1 word = 5 non-space chars)
# =========================
# def count_words(text):
#     if not text:
#         return 0
#     char_count = len(text.replace(" ", ""))
#     return math.ceil(char_count / 5)

# async def call_openai_video_model(model_id, api_key, user_id, prompt, duration, width, height, seed, base_cost):
#     client = AsyncOpenAI(api_key=api_key)

#     if not prompt or prompt.strip() == "":
#         return {"error": "Prompt cannot be empty"}
    
#     # Standardize duration/resolution
#     try:
#         duration = int(duration)
#     except:
#         duration = 4

#     if duration not in [4, 8, 12]:
#         return {"error": "Invalid duration. Allowed values are 4, 8, or 12 seconds."}
    
#     if model_id not in ['sora-2', 'sora-2-pro']:
#          # Defaulting to sora-2 if invalid but keeping user check logic
#          return {"error": "Invalid model ID. Contact to admin."}
    
#     possible_resolutions = ["720x1280", "1280x720", "1024x1792", "1792x1024"]
#     if f"{width}x{height}" not in possible_resolutions:
#         return {"error": f"Invalid resolution. Allowed resolutions are: {', '.join(possible_resolutions)}"}
#     # Check resolution simplified
#     size = f"{width}x{height}"

#     try:
#         # Sync DB fetch via sync_to_async
#         user = await sync_to_async(User.objects.get)(id=user_id)
#         credit_account = await sync_to_async(CreditAccount.objects.get)(user=user)
#     except Exception:
#         return {"error": "User or Credit Account not found"}

#     # Calculate total cost (assuming base_cost is per second or flat, here we follow user's pattern)
#     # If base_cost is per request as current code suggests:
#     total_cost= Decimal(str(base_cost))* Decimal(str(duration))
#     if credit_account.credits < total_cost:
#         return {"error": "Insufficient credits to perform this operation."}

#     # Word count for tracking (if needed)
#     prompt_words = count_words(prompt)

#     try:
#         # Start generation
#         # Updated to use .create() as .generate() is not a valid method on AsyncVideos
#         response = await client.videos.create(
#             model=model_id,
#             prompt=prompt,
#             seconds=duration, # Updated argument name from duration to seconds
#             size=f"{width}x{height}", # Combined width and height into size
#         )
#     except Exception as e:
#         print("Error generating video with OpenAI:", e)
#         return {"error": f"AI error: {str(e)}"}

#     # Polling Loop (Non-blocking)
#     start_time = time.time()
#     video_url = []
    
#     while True:
#         # Check for timeout (10 mins)
#         print("I am in the while loop of openai video function")
#         if time.time() - start_time > 600:
#             return {"error": "Video generation timed out"}
            
#         # Access status/id safely
#         status = getattr(response, 'status', None)
#         if not status:
#              # Fallback if status not present
#              return {"error": "Unable to determine video generation status."}

#         if status == "completed":
#             # Atomic deduction
#             @sync_to_async
#             def _deduct():
#                 with transaction.atomic():
#                     ca = CreditAccount.objects.select_for_update().get(id=credit_account.id)
#                     ca.credits -= total_cost
#                     ca.save(update_fields=['credits'])
                    
#                     u = User.objects.get(id=user_id)
#                     u.total_token_used += total_cost
#                     u.save(update_fields=['total_token_used'])
                    
#                     # Video models don't track words against subscription
#                     # trackUsedWords(user_id, prompt_words)
            
#             await _deduct()

#             # Extract URLs - assuming standard response object structure
#             # Extract URLs - handling different response structures
#             # Extract URLs - handling different response structures
#             # Check 'output' (standard for some endpoints)
#             if hasattr(response, 'output'):
#                 if isinstance(response.output, list):
#                     for item in response.output:
#                         if hasattr(item, 'url'): video_url.append(item.url)
#                         elif isinstance(item, dict) and 'url' in item: video_url.append(item['url'])
#                 elif hasattr(response.output, 'url'):
#                      video_url.append(response.output.url)
            
#             # Check 'data' (common in other OpenAI endpoints)
#             if hasattr(response, 'data'):
#                 if isinstance(response.data, list):
#                     for item in response.data:
#                         if hasattr(item, 'url'): video_url.append(item.url)
#                         elif isinstance(item, dict) and 'url' in item: video_url.append(item['url'])
            
#             # Check top-level 'url' attribute
#             if hasattr(response, 'url'):
#                 video_url.append(response.url)

#             if not video_url:
#                  print(f"DEBUG: Response object keys: {response.__dict__ if hasattr(response, '__dict__') else 'No dict'}")
#                  return {"error": "Video generated but no URL found in response."}

#             return {
#                 "text": f"Video generated successfully ({duration}s).",
#                 "images": video_url,
#                 "sender": "ai"
#             }
            
#         elif status in ["queued", "processing", "pending"]:
#             await asyncio.sleep(5) # Reduced sleep to 5s for responsiveness, increases to 10s if needed
#             try:
#                 # Retrieve updated status
#                 response = await client.videos.retrieve(response.id)
#                 print(f"Video status: {response.status}")
#             except Exception as e:
#                 print(f"Error polling video status: {e}")
#                 # Don't fail immediately on individual poll fail, maybe retry
#                 await asyncio.sleep(5)
#         else:
#             return {"error": f"Video generation failed with status: {status}"}
