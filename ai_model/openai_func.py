from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from openai import OpenAI

from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords

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

    try:
        # Execute the model request
        if model_type in {"chat", "completion", "image_understanding"}:
            messages = []

            if summary:
                messages.append({
                    "role": "system",
                    "content": summary
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
            if f"{width}x{height}" not in ["1024x1024","1536x1024"]:
                width=1024
                height=1024
            res = client.images.generate(
                model=model_id,
                prompt=message,
                n=num_images,
                size=f"{width}x{height}",
            )

            text = f"{num_images} image(s) generated"
            images = [img.url for img in res.data]

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
        elif model_type=="video_generation":
            job = client.videos.create(
                model="sora-2", # user specified model
                prompt=message or "Video generation", 
                seconds=int(duration),
                size=f"{width}x{height}"
                )

            text = f"Video generation started: {getattr(job, 'id', 'unknown')}"
            # No images/video URL yet if async?
            
        return {
            "text": text or "",
            "images": images or [],
            "sender": "ai",
            "error": None,
        }

    except Exception as e:
        # Refund on failure
        with transaction.atomic():
            credit_account.credits += charge_amount
            credit_account.save(update_fields=["credits"])

            user.total_token_used -= charge_amount
            user.save(update_fields=["total_token_used"])

        return _error(str(e))


# Helpers
def _error(msg: str) -> dict:
    return {
        "text": "",
        "images": [],
        "sender": "system",
        "error": msg,
    }

#     return "unknown"


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

    if "sora" in model or "video" in model:
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
