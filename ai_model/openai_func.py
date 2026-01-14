# from django.contrib.auth import get_user_model
# from accounts.models import CreditAccount
# from openai import OpenAI
# from .track_used_word_subscription import trackUsedWords
# import base64
# from .image_to_url_save import download_and_store_webp
# User = get_user_model()

# # Cache to avoid calling OpenAI every time
# MODEL_CACHE = {}

# def get_model_limits(model_name,client):
    
#     # Return cached limits
#     if model_name in MODEL_CACHE:
#         return MODEL_CACHE[model_name]

#     try:
#         model_info = client.models.retrieve(model_name)

#         input_limit = model_info.capabilities.get("input_tokens", 16000)
#         output_limit = model_info.capabilities.get("output_tokens", 4096)

#         MODEL_CACHE[model_name] = {
#             "input": input_limit,
#             "output": output_limit
#         }

#         return MODEL_CACHE[model_name]

#     except Exception:
#         # fallback for unknown future models
#         return {
#             "input": 16000,
#             "output": 4096
#         }


# def get_dynamic_max_tokens(model_name,client,requested_max):
#     limits = get_model_limits(model_name,client=client)
#     output_limit = limits["output"]

#     # Clamp to the model's limit
#     return min(requested_max, output_limit)

# def gpt_response(
#     message: str,
#     model_id: str,
#     api_key: str,
#     user_id: int,
#     images_data_list: list[str] | None = None,
#     width=None,
#     height=None,
#     summary=None,
#     audio_data: str | None = None,
#     max_response_tokens: int = 0,
#     num_images=1,
#     base_cost=500,

# ) -> dict:
#     try:
#         client = OpenAI(api_key=api_key)

#         user = User.objects.filter(id=user_id).first()
#         if not user:
#             return _error("User not found.")

#         credit_account = CreditAccount.objects.filter(user=user).first()
#         if not credit_account:
#             return _error("Credit account not found.")

#         context_list=[]
#         if summary:
#             context_list.append(
#                 {
#         "role": "system",
#         "content": f"Conversation summary so and listen don't show or response this summary to user just use this to track then context much better way here summary: {summary}"
#                 }
#             )
#         prompt_words = len(message.split())
#         prompt_words_cost=prompt_words*base_cost
        

#         context_list.append({
#         "role": "user",
#         "content": f'if you are not an image model and user say you to generate image and if you can not analize image but user say you for analize image just give them proper response that you can not do this .Here the prompt that user says to you: {message} follow it anyway'
#         })

        
        
#         if credit_account.credits < prompt_words_cost:
#             return _error("Insufficient credits for prompt.")
        

         
#         credit_account.credits -= prompt_words_cost
#         credit_account.save()
#         user.total_token_used+=prompt_words_cost
#         user.save()
#         trackUsedWords(user.id,prompt_words)

#         # max_response_tokens = int(credit_account.credits * 1.33)

#         # if max_response_tokens<=0:
#         #     return _error(f"You don't have enough credit's to gate response")
#         # print(max_response_tokens)
#         max_response_tokens=4096
#         max_response_tokens=get_dynamic_max_tokens(model_name=model_id,client=client,requested_max=max_response_tokens)
#         print(max_response_tokens)
        

       

        

#         model_lower = model_id.lower()
#         model_type = _detect_model_type(model_lower, images_data_list, audio_data)
#         print(model_type)

#         if model_type!="chat":
        
#             base_cost=base_cost #words
#             num_images =1
#             total_words=base_cost*num_images

#             if total_words>credit_account.credits:
#                 credit_account.credits+=prompt_words_cost
#                 credit_account.save()
                
                   
#                 return _error(f"You Don't have enought credits to generate image")
#             credit_account.credits-=total_words
#             credit_account.save()
#             trackUsedWords(user.id,prompt_words)
        
            

#         text, images = "", []

        
#         if model_type == "chat":
#             text = _chat_request(client, model_id,context_list, max_response_tokens)

#         elif model_type == "completion":
#             text = _completion_request(client, model_id, context_list, max_response_tokens)

#         elif model_type == "image_understanding":
#             text = _vision_request(client, model_id, context_list, images_data_list, max_response_tokens)

#         elif model_type == "image_generation":
#             text, images = _image_request(client, model_id, context_list,width,
#     height,num_images=num_images)

#         elif model_type == "audio_generation":
#             text = _audio_request(client, model_id, context_list, audio_data)

#         elif model_type == "embedding":
#             text = _embedding_request(client, model_id, context_list)

#         elif model_type == "moderation":
#             text = _moderation_request(client, model_id, context_list)

#         else:
#             return _error(f"Unsupported model type for '{model_id}'.")

#         response_words = len(text.split())
#         if (response_words*base_cost) > credit_account.credits:
#             allowed = (credit_account.credits/base_cost) if credit_account!=0 else 0
#             text = " ".join(text.split()[:allowed])
#             response_words = allowed

#         credit_account.credits -= response_words*base_cost
#         credit_account.save()
#         user.total_token_used+=response_words*base_cost
#         user.save()

#         trackUsedWords(user.id,response_words)

#         return {"text": text, "images": images, "sender": "ai", "error": None}

#     except Exception as e:

#         try:
#             if 'credit_account' in locals():
#                 credit_account.credits += prompt_words
#                 user.total_token_used-=prompt_words
#                 if model_type=="image_generation":
#                     total_cost=base_cost*num_images
#                     credit_account.credits += total_cost
#                     user.total_token_used-=total_cost
#                 user.save()
#                 credit_account.save()
#         except Exception:
#             pass

    
#         error_message = str(e)
#         if "billing_hard_limit_reached" in error_message:
#             error_message = "OpenAI billing limit reached for this account."
#         elif "not allowed to sample" in error_message:
#             error_message = "Selected model not available or unauthorized."
#         elif "insufficient_quota" in error_message:
#             error_message = "Your OpenAI quota has been exceeded."

#         return _error(f"GPT request failed: {error_message}")




#

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from openai import OpenAI

from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords

User = get_user_model()


# =========================
# COST CALCULATION
# =========================
def calculate_cost(model_type, *, base_cost, words=0, num_images=1,secounds=4):
    base_cost = Decimal(str(base_cost))

    if model_type in {"chat", "completion"}:
        return Decimal(words) * base_cost

    if model_type == "image_generation":
        return Decimal(num_images) * base_cost
    
    if model_type=="video_generation":
        return Decimal(secounds)*base_cost

    if model_type in {
        "image_understanding",
        "audio_generation",
        "embedding",
        "moderation",
    }:
        return base_cost  # flat cost

    return Decimal("0")

import time
# =========================
# MAIN ENTRY
# =========================
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
):

   
    client = OpenAI(api_key=api_key)

    user = User.objects.filter(id=user_id).first()
    if not user:
        return _error("User not found")

    model_type = _detect_model(
        model_id.lower()
    )


    print("---------------model type--------------",model_type)

    prompt_words = len(message.split())

    charge_amount = calculate_cost(
        model_type,
        base_cost=base_cost,
        words=prompt_words,
        num_images=num_images,
    )

    # =========================
    # CREDIT DEDUCTION (SAFE)
    # =========================
    with transaction.atomic():
        credit_account = (
            CreditAccount.objects
            .select_for_update()
            .filter(user=user)
            .first()
        )

        if not credit_account:
            return _error("Credit account not found")

        if credit_account.credits < charge_amount:
            return _error("Insufficient credits")

        credit_account.credits -= charge_amount
        credit_account.save(update_fields=["credits"])

        user.total_token_used += charge_amount
        user.save(update_fields=["total_token_used"])

        trackUsedWords(user.id, prompt_words)

    try:
        # =========================
        # MODEL EXECUTION
        # =========================
        if model_type in {"chat", "completion"}:
            messages = []

            if summary:
                messages.append({
                    "role": "system",
                    "content": summary
                })

            messages.append({
                "role": "user",
                "content": message
            })

            res = client.chat.completions.create(
                model=model_id,
                messages=messages,
            )

            text = res.choices[0].message.content.strip()
            images = []

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

        elif model_type == "image_understanding":
            res = client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            [{"type": "text", "text": message}] +
                            [
                                {"type": "image_url", "image_url": {"url": img}}
                                for img in images_data_list
                            ]
                        ),
                    }
                ],
            )

            text = res.choices[0].message.content.strip()
            images = []

        elif model_type == "audio_generation":
            res = client.audio.transcriptions.create(
                model=model_id,
                file=audio_data,
            )

            text = res.text.strip()
            images = []

        elif model_type == "embedding":
            res = client.embeddings.create(
                model=model_id,
                input=message,
            )

            text = str(res.data[0].embedding)
            images = []

        elif model_type == "moderation":
            res = client.moderations.create(
                model=model_id,
                input=message,
            )

            text = str(res.results[0])
            images = []
        elif model_type=="video_generation":
            print("viddooooooooooooooooooooooooooooooooo")
            if f"{width}x{height}" not in ["720x1280","1280x720"]:
                width=720
                height=1280

            job = client.videos.create(
                model="sora-2",
                prompt="A cinematic shot of a tiger walking through a jungle at sunrise",
                seconds=duration,
                size="720x1280"
            
                )
            print(job)
            # while True:
            #     result = client.videos.retrieve(job.id)
            #     if result.status == "completed":
            #         print(result.output[0].url)
            #         break
            #     elif result.status=="in_progress":
            #         print("the video is processing")
            #         time.sleep(5)
            #     elif result.status == "failed":
            #         raise Exception("Video generation failed")

            #     else:
            #           print("Unknown video status:", result.status)

        return {
            "text": text or "",
            "images": images or [],
            "sender": "ai",
            "error": None,
        }

    except Exception as e:
        # =========================
        # EXACT REFUND (SAFE)
        # =========================
        with transaction.atomic():
            credit_account.credits += charge_amount
            credit_account.save(update_fields=["credits"])

            user.total_token_used -= charge_amount
            user.save(update_fields=["total_token_used"])

        return _error(str(e))


# =========================
# HELPERS
# =========================
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
