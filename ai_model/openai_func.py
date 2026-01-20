from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from openai import OpenAI

from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords
from .image_to_url_save import download_and_store_video

User = get_user_model()




# Helper: Calculate costs based on model type
def calculate_cost(model_type, *, base_cost, words=0, num_images=1, secounds=4, input_images_count=0):
    base_cost = Decimal(str(base_cost))

    if model_type in {"chat", "completion", "image_understanding"}:
        # Charge for words + input images (flat fee per image)
        return (Decimal(words) * base_cost) + (Decimal(input_images_count) * base_cost)

    if model_type == "image_generation":
        return Decimal(num_images) * base_cost
    
    if model_type == "video_generation":
        return Decimal(secounds) * base_cost

    if model_type in {
        "audio_generation",
        "embedding",
        "moderation",
    }:
        return base_cost  # flat cost

    return Decimal(base_cost)

import time





#helper function for video generation
# def video_generatio()


def gpt_response(
    message: str,
    model_id: str,
    api_key: str,
    user_id: int,
    base_cost=100,
    images_data_list=None,
    audio_data=None,
    num_images=1,
    summary=None,
    height=1024,
    width=1024,
    duration=4,
    aspect_ratio=None 
):

   
    client = OpenAI(api_key=api_key)

    user = User.objects.filter(id=user_id).first()
    if not user:
        return _error("User not found")

    model_type = _detect_model(model_id.lower())

    prompt_words = len(message.split())
    input_images_count = len(images_data_list) if images_data_list else 0
    if model_type=="video_generation":
        size=f"{width}x{height}"
        if model_id=="sora-2":
            if size not in ["720x1280","1280x720"]:
                    size="1280x720"
        if model_id=="sora-2-pro":
                size_list=["1280x720","720x1280","1024x1792","1792x1024"]
                if size not in size_list:
                    size="1280x720"
                else:
                    import math
                    if size in ["1280x720","720x1280"]:
                        base_cost=Decimal(base_cost)*1
                    else:
                        base_cost=math.ceil(Decimal(base_cost)*1.67)
    charge_amount = calculate_cost(
        model_type,
        base_cost=base_cost,
        words=prompt_words,
        num_images=num_images,
        secounds=duration,
        input_images_count=input_images_count
    )

    # Deduct credits atomically
    with transaction.atomic():
        credit_account = CreditAccount.objects.select_for_update().filter(user=user).first()
        if not credit_account:
            return _error("Credit account not found")

        if credit_account.credits < charge_amount:
            return _error(f"Insufficient credits. Required: {charge_amount}")

        credit_account.credits -= charge_amount
        credit_account.save(update_fields=["credits"])

        user.total_token_used += charge_amount
        user.save(update_fields=["total_token_used"])

        trackUsedWords(user.id, prompt_words)
        
        # Calculate remaining credits to determine max output
        remaining_credits = credit_account.credits
        
        if base_cost > 0:
            max_response_words = int(remaining_credits / Decimal(str(base_cost)))
        else:
            max_response_words = 4096 

        # If insufficient for any output, refund and exit
        if max_response_words < 1 and model_type in {"chat", "completion", "image_understanding"}:
             credit_account.credits += charge_amount
             credit_account.save(update_fields=["credits"])
             user.total_token_used -= charge_amount
             user.save(update_fields=["total_token_used"])
             return _error("Insufficient credits for response.")
        
        # Cap at safe limit
        final_max_tokens = min(max_response_words, 4096)

    text = ""
    images = []

    try:
        # Execute the model request
        if model_type in {"chat", "completion", "image_understanding"}:
            messages = []

            # Add a base system prompt for language and behavior
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant. Please respond in English by default, unless the user explicitly asks in another language or the context requires it."
            })

            if summary:
                messages.append({
                    "role": "system",
                    "content": f"Conversation summary so far: {summary}. Use this for context only."
                })

            # Construct multimodal user message if images exist
            user_content = []
            if message:
                user_content.append({"type": "text", "text": message})
            
            if images_data_list:
                for img_url in images_data_list:
                    user_content.append({
                        "type": "image_url", 
                        "image_url": {"url": img_url}
                    })
            
            if not user_content:
                user_content = " "

            messages.append({
                "role": "user",
                "content": user_content
            })

            res = client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=final_max_tokens  # Force limit based on credits
            )

            text = res.choices[0].message.content.strip()
            # images = [] # Already init

            # Deduct the cost for generated text output
            if text:
                response_words = len(text.split())
                response_cost = calculate_cost(
                    model_type,
                    base_cost=base_cost,
                    words=response_words
                )
                
                with transaction.atomic():
                     credit_account_updated = CreditAccount.objects.select_for_update().filter(user=user).first()
                     if credit_account_updated:
                        credit_account_updated.credits -= response_cost
                        credit_account_updated.save(update_fields=["credits"])
                        
                        user.total_token_used += response_cost
                        user.save(update_fields=["total_token_used"])
                        
                        trackUsedWords(user.id, response_words)

        elif model_type == "image_generation":
            # DALL-E 3 only supports n=1
            gen_n = num_images
            if "dall-e-3" in model_id.lower():
                gen_n = 1
            
            # Support standard DALL-E sizes
            current_size = f"{width}x{height}"
            allowed_dalle3_sizes = ["1024x1024", "1792x1024", "1024x1792"]
            if "dall-e-3" in model_id.lower() and current_size not in allowed_dalle3_sizes:
                current_size = "1024x1024"
            elif "dall-e-2" in model_id.lower() and current_size not in ["256x256", "512x512", "1024x1024"]:
                current_size = "1024x1024"

            print(f"DEBUG: Generating {gen_n} image(s) with {model_id} (requested size: {width}x{height}, using: {current_size})")
            
            res = client.images.generate(
                model=model_id,
                prompt=message,
                n=gen_n,
                size=current_size,
            )

            text = f"{gen_n} image(s) generated."
            images = [img.url for img in res.data]
            print(f"DEBUG: Image generation success. URLs count: {len(images)}")

        elif model_type == "audio_generation":
            res = client.audio.transcriptions.create(
                model=model_id,
                file=audio_data,
            )

            text = res.text.strip()
            # images = []

        elif model_type == "embedding":
            res = client.embeddings.create(
                model=model_id,
                input=message,
            )

            text = str(res.data[0].embedding)
            # images = []

        elif model_type == "moderation":
            res = client.moderations.create(
                model=model_id,
                input=message,
            )

            text = str(res.results[0])
            # images = []
        elif model_type == "video_generation":
            images, text = _handle_openai_video_generation(client, model_id, message, duration, size)

        return {
            "text": text or "",
            "images": images or [],
            "sender": "ai",
            "error": None,
        }

    except Exception as e:
        error_str = str(e)
        print(f"ERROR in gpt_response: {error_str}")
        
        # Refund on failure if credits were deducted
        try:
            if 'charge_amount' in locals() and 'credit_account' in locals() and credit_account:
                with transaction.atomic():
                    # Refresh credit account to be safe
                    ca = CreditAccount.objects.select_for_update().filter(user=user).first()
                    if ca:
                        ca.credits += charge_amount
                        ca.save(update_fields=["credits"])

                        user.total_token_used -= charge_amount
                        user.save(update_fields=["total_token_used"])
                        print(f"DEBUG: Refunded {charge_amount} credits due to error.")
        except Exception as refund_err:
            print(f"ERROR during refund: {refund_err}")

        # Sanitize error message for user
        if "api_key" in error_str.lower() or "api key" in error_str.lower() or "incorrect api" in error_str.lower():
            return _error("Authentication failed: Invalid API key or configuration.")
        
        return _error(f"Request failed. Please try again later.")


# Helpers
def _error(msg: str) -> dict:
    return {
        "text": "",
        "images": [],
        "sender": "system",
        "error": msg,
    }

#     return "unknown"


def _handle_openai_video_generation(client, model_id, message, duration, size):
    """
    Helper to handle OpenAI video generation (Sora) using the client.videos.create method.
    Returns (images_list, text_response).
    """
    import time
    from .image_to_url_save import download_and_store_video

    # Format seconds as string, allowed values: 4, 8, 12
    try:
        sec = int(duration)
        if sec not in [4, 8, 12]:
            sec = 4
    except:
        sec = 4
    seconds_str = str(sec)

    # Allowed sizes as per documentation: 720x1280, 1280x720, 1024x1792, 1792x1024
    allowed_sizes = ["720x1280", "1280x720", "1024x1792", "1792x1024"]
    if size not in allowed_sizes:
        # Try finding a closest match or default
        size = "1280x720"

    print(f"DEBUG: Initiating Sora video generation: model={model_id}, seconds={seconds_str}, size={size}")

    # Call the correct endpoint: client.videos.create
    try:
        response = client.videos.create(
            model=model_id,
            prompt=message or "Video generation",
            seconds=seconds_str,
            size=size
        )
    except Exception as e:
        raise Exception(f"Video API Error: {str(e)}")
    
    job_id = getattr(response, 'id', None)
    if not job_id:
        # Fallback for different SDK versions
        job_id = getattr(response, 'data', [{}])[0].get('id') if hasattr(response, 'data') else None

    if not job_id:
        raise Exception("Failed to retrieve Job ID from OpenAI video generation response.")

    video_url = None
    max_attempts = 120  # ~10 minutes
    
    for i in range(max_attempts):
        # Refresh status using the job ID
        try:
            job = client.videos.retrieve(job_id)
            if job.status == "completed":
                # Extract URL
                if hasattr(job, 'url') and job.url:
                    video_url = job.url
                elif hasattr(job, 'data') and len(job.data) > 0:
                    video_url = job.data[0].url
                break
            
            if job.status == "failed":
                error_details = getattr(job, 'last_error', None) or getattr(job, 'error', 'Unknown provider error')
                raise Exception(f"Video generation failed: {error_details}")
        except Exception as poll_err:
            print(f"DEBUG: Polling error (attempt {i+1}): {poll_err}")
            # Continue polling unless it's a fatal failure
        
        time.sleep(5)
    
    if not video_url:
        raise Exception("Video generation timed out or no video URL found in completed job.")
    
    # Download and store locally
    try:
        saved_videos = download_and_store_video(video_url)
        if saved_videos and saved_videos[0]:
            return [saved_videos[0]], "Video generated successfully."
    except Exception as e:
        print(f"Error downloading Sora video: {e}")
        
    return [video_url], f"Video generated but local storage failed. URL: {video_url}"





def _detect_model(model_id: str) -> str:
    """
    Safe, model-id–only detection.
    Works for all current & future models.
    """

    if not model_id:
        return "Unknown"

    model = model_id.lower()

    # -------------------------
    # STRICT / HIGH-CONFIDENCE
    # -------------------------

    if "sora-2" in model or "sora-2-pro" in model:
        return "video_generation"

    if "image" in model or "dall-e" in model or "img" in model:
        return "image_generation"

    if "vision" in model:
        return "image_understanding"

    if "audio" in model or "tts" in model or "stt" in model:
        return "audio_generation"

    if "embed" in model:
        return "embedding"

    if "moderation" in model or "safety" in model:
        return "moderation"

    # -------------------------
    # LEGACY COMPLETIONS
    # -------------------------

    if any(k in model for k in ("davinci", "curie", "babbage", "ada")):
        return "completion"

    # -------------------------
    # DEFAULT (SAFE)
    # -------------------------
    # All modern & future models support chat semantics
    if "gpt" in model or "o1" in model or "o3" in model:
        return "chat"

    return "unknown"



# def _detect_model_type(model_lower: str, images_data_list, audio_data) -> str:
#     if any(k in model_lower for k in ["dall-e", "gpt-image", "image-gen"]):
#         return "image_generation"

#     if images_data_list and any(k in model_lower for k in ["vision", "gpt-4o", "gpt-4-vision"]):
#         return "image_understanding"

#     if audio_data and any(k in model_lower for k in ["audio", "tts", "gpt-audio"]):
#         return "audio_generation"

#     if any(k in model_lower for k in ["embedding", "text-embedding"]):
#         return "embedding"

#     if any(k in model_lower for k in ["moderation", "omni-moderation"]):
#         return "moderation"

#     if any(k in model_lower for k in ["davinci", "curie", "babbage", "ada"]):
#         return "completion"

#     if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
#         return "chat"
