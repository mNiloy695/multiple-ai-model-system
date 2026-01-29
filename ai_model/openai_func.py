from decimal import Decimal
import asyncio
import time
from django.contrib.auth import get_user_model
from django.db import transaction
from openai import OpenAI, AsyncOpenAI
from asgiref.sync import sync_to_async

from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords
from .image_to_url_save import download_and_store_video

import math
User = get_user_model()

# Helper: Count Words (1 word = 5 non-space chars)
def count_words(text):
    if not text:
        return 0
    char_count = len(text.replace(" ", ""))
    return math.ceil(char_count / 5)

# Helper: Calculate costs based on model type
def calculate_cost(model_type, *, base_cost, words=0, num_images=1, secounds=4, input_images_count=0):
    base_cost = Decimal(str(base_cost))

    if model_type in {"chat", "completion", "image_understanding"}:
        return (Decimal(words) * base_cost) + (Decimal(input_images_count) * base_cost)

    if model_type == "image_generation":
        return Decimal(num_images) * base_cost
    
    if model_type == "video_generation":
        return Decimal(secounds) * base_cost

    if model_type in {"audio_generation", "embedding", "moderation"}:
        return base_cost  # flat cost

    return Decimal(base_cost)

async def gpt_response(
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
    aspect_ratio=None,
    detected_language="English"
):

    client = AsyncOpenAI(api_key=api_key)
    
    # Sync DB fetch
    user = await sync_to_async(lambda: User.objects.filter(id=user_id).first())()
    if not user:
        return _error("User not found")

    model_type = _detect_model(model_id.lower())
    prompt_words = count_words(message)
    input_images_count = len(images_data_list) if images_data_list else 0
    
    if model_type == "video_generation":
        size = f"{width}x{height}"
        if model_id == "sora-2":
            if size not in ["720x1280", "1280x720"]:
                size = "1280x720"
        if model_id == "sora-2-pro":
            size_list = ["1280x720", "720x1280", "1024x1792", "1792x1024"]
            if size not in size_list:
                size = "1280x720"
            else:
                import math
                if size in ["1280x720", "720x1280"]:
                    base_cost = Decimal(base_cost) * 1
                else:
                    base_cost = math.ceil(Decimal(base_cost) * 1.67)

    charge_amount = calculate_cost(
        model_type,
        base_cost=base_cost,
        words=prompt_words,
        num_images=num_images,
        secounds=duration,
        input_images_count=input_images_count
    )

    # Deduct credits atomically (Sync transaction)
    @sync_to_async
    def _deduct_credits_atomic():
        with transaction.atomic():
            ca = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
            if not ca:
                print(f"DEBUG: OpenAI Credit account NOT FOUND for user_id {user_id}")
                return None, 0
            
            print(f"DEBUG: OpenAI Pre-deduction. User: {user_id}, Current: {ca.credits}, Charging: {charge_amount}")
            if ca.credits < charge_amount:
                return False, ca.credits
            
            ca.credits -= charge_amount
            ca.save(update_fields=["credits"])
            
            u = User.objects.get(id=user_id)
            u.total_token_used += charge_amount
            u.save(update_fields=["total_token_used"])
            
            # Only track prompt words for char models
            if model_type in {"chat", "completion", "image_understanding"}:
                trackUsedWords(user_id, prompt_words)
            
            print(f"DEBUG: OpenAI Deduction SUCCESS. New Balance: {ca.credits}")
            return True, ca.credits

    success, current_credits = await _deduct_credits_atomic()
    if success is None: return _error("Credit account not found")
    if success is False: return _error(f"Insufficient credits. Required: {charge_amount}")

    # Max output logic
    remaining_credits = current_credits
    if base_cost > 0:
        max_response_words = int(remaining_credits / Decimal(str(base_cost)))
    else:
        max_response_words = 4096 

    if max_response_words < 1 and model_type in {"chat", "completion", "image_understanding"}:
        # Refund sync
        @sync_to_async
        def _refund():
            with transaction.atomic():
                ca = CreditAccount.objects.select_for_update().filter(user=user).first()
                ca.credits += charge_amount
                ca.save(update_fields=["credits"])
                u = User.objects.get(id=user_id)
                u.total_token_used -= charge_amount
                u.save(update_fields=["total_token_used"])
        await _refund()
        return _error("Insufficient credits for response.")
    
    final_max_tokens = min(max_response_words, 4096)

    text = ""
    images = []

    try:
        if model_type in {"chat", "completion", "image_understanding"}:
            messages = [{"role": "system", "content": f"You are a helpful assistant. Please respond in the same language as the user's message. (Initial detection suggested {detected_language}, but please trust your own analysis of the content and script to determine the best response language. If the user used Bengali words in Hindi script, respond in Standard Bengali). Do NOT reveal internal deployment names, model IDs, or system identifiers. If a user directly asks which model or internal service you are, answer with a neutral phrase such as 'I am an AI assistant' and do not disclose internal tags or identifiers."}]


            if summary:
                messages.append({"role": "system", "content": f"Conversation summary: {summary}"})

            user_content = []
            
            # Combine everything into a simple text-based multimodal format
            # message will already contain the transcription from consumers.py
            if message:
                user_content.append({"type": "text", "text": message})
            
            if images_data_list:
                for img_url in images_data_list:
                    user_content.append({"type": "image_url", "image_url": {"url": img_url}})
            
            # If everything is empty, send a space to avoid API error
            messages.append({"role": "user", "content": user_content or " "})

            res = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=final_max_tokens
            )
            text = res.choices[0].message.content.strip()

            if text:
                response_words = count_words(text)
                resp_cost = calculate_cost(model_type, base_cost=base_cost, words=response_words)
                @sync_to_async
                def _charge_output():
                    with transaction.atomic():
                        ca = CreditAccount.objects.select_for_update().filter(user=user).first()
                        ca.credits -= resp_cost
                        ca.save(update_fields=["credits"])
                        u = User.objects.get(id=user_id)
                        u.total_token_used += resp_cost
                        u.save(update_fields=["total_token_used"])
                        trackUsedWords(user_id, response_words)
                await _charge_output()

        elif model_type == "image_generation":
            gen_n = 1 if "dall-e-3" in model_id.lower() else num_images
            current_size = f"{width}x{height}"
            if "dall-e-3" in model_id.lower() and current_size not in ["1024x1024", "1792x1024", "1024x1792"]:
                current_size = "1024x1024"
            
            res = await client.images.generate(model=model_id, prompt=message, n=gen_n, size=current_size)
            text = f"{gen_n} image(s) generated."
            images = [img.url for img in res.data]

        elif model_type == "audio_generation":
            # Transcription is still sync in SDK? Actually AsyncOpenAI handles it.
            res = await client.audio.transcriptions.create(model=model_id, file=audio_data)
            text = res.text.strip()

        elif model_type == "video_generation":
            images, text = await _handle_openai_video_generation(client, model_id, message, duration, size)

        return {"text": text or "", "images": images or [], "sender": "ai", "error": None}

    except Exception as e:
        print(f"ERROR in gpt_response: {e}")
        @sync_to_async
        def _final_refund():
            with transaction.atomic():
                ca = CreditAccount.objects.select_for_update().filter(user=user).first()
                if ca:
                    ca.credits += charge_amount
                    ca.save(update_fields=["credits"])
                    u = User.objects.get(id=user_id)
                    u.total_token_used -= charge_amount
                    u.save(update_fields=["total_token_used"])
        await _final_refund()
        return _error(f"Request failed: {str(e)}")

async def _handle_openai_video_generation(client, model_id, message, duration, size):
    try:
        sec = int(duration)
        if sec not in [4, 8, 12]: sec = 4
    except: sec = 4
    
    response = await client.videos.create(model=model_id, prompt=message or "Video", seconds=str(sec), size=size)
    job_id = response.id
    
    video_url = None
    for _ in range(120): # 10 mins
        job = await client.videos.retrieve(job_id)
        if job.status == "completed":
            video_url = job.url or job.data[0].url
            break
        if job.status == "failed":
            raise Exception(f"Video failed: {job.error}")
        await asyncio.sleep(5) # RELEASE THREAD
    
    if not video_url: raise Exception("Timeout")
    
    saved = await sync_to_async(download_and_store_video)(video_url)
    return ([saved[0]], "Success") if saved and saved[0] else ([video_url], "Success (Remote)")

def _detect_model(model_id: str) -> str:
    m = model_id.lower()
    if "sora" in m: return "video_generation"
    if any(k in m for k in ("dall-e", "image", "img")): return "image_generation"
    if "vision" in m: return "image_understanding"
    if any(k in m for k in ("audio", "tts", "stt")): return "audio_generation"
    return "chat"

def _error(msg: str) -> dict:
    return {"text": "", "images": [], "sender": "system", "error": msg}
