from decimal import Decimal
import asyncio
import time
import requests
import base64
from django.contrib.auth import get_user_model
from django.db import transaction
from google import genai
from google.genai import types
from asgiref.sync import sync_to_async

from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords
from .image_to_url_save import download_and_store_webp

import math
User = get_user_model()

# =========================
# HELPER: Count Words (1 word = 5 non-space chars)
# =========================
def count_words(text):
    if not text:
        return 0
    # Remove spaces and calculate ceil(len/5)
    char_count = len(text.replace(" ", ""))
    return math.ceil(char_count / 5)
def calculate_cost(model_type, *, base_cost, words=0, num_images=1, input_images_count=0):
    base_cost = Decimal(str(base_cost))

    if model_type in {"chat", "text_generation", "code_generation", "image_understanding"}:
        return (Decimal(words) * base_cost) + (Decimal(input_images_count) * base_cost)

    if model_type == "image_generation" or model_type == "text_to_image":
        return Decimal(num_images) * base_cost
    
    return Decimal(base_cost)

# =========================
# HELPER: Detect Model Type
# =========================
def _detect_model_type(model_id):
    ml = model_id.lower()
    if any(x in ml for x in ["image", "img", "gen", "photo", "art", "text_to_image"]):
        return "text_to_image"
    return "chat"

# =========================
# HELPER: Error Response
# =========================
def _error(msg):
    return {"text": "", "images": [], "sender": "system", "error": msg}

# =========================
# HELPER: Read Image
# =========================
async def _read_image_to_base64_async(img):
    try:
        if img.startswith("http"):
            resp = await sync_to_async(requests.get)(img, timeout=30)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
        return img
    except Exception:
        return None

# =========================
# MAIN FUNCTION
# =========================
async def gemini_response(
    message,
    model_id,
    api_key,
    user_id,
    images_data_list=None,
    summary=None,
    num_images=1,
    base_cost=500,
    width=None,
    height=None,
    model_type=None,
    resolution="720p",
    detected_language="English"
):

    try:
        client = genai.Client(api_key=api_key)

        user = await sync_to_async(lambda: User.objects.filter(id=user_id).first())()
        if not user:
            return _error("User not found.")

        if not model_type:
            model_type = _detect_model_type(model_id)

        num_images = 1 # Force 1 image per request
        
        prompt_words = count_words(message)
        input_images_count = len(images_data_list) if images_data_list else 0
        
        charge_amount = calculate_cost(
            model_type,
            base_cost=base_cost,
            words=prompt_words,
            num_images=num_images,
            input_images_count=input_images_count
        )

        # Credit Deduction (Atomic)
        @sync_to_async
        def _deduct_credits_atomic():
            with transaction.atomic():
                acc = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
                if not acc: 
                    print(f"DEBUG: Credit account NOT FOUND for user_id {user_id}")
                    return None, 0
                
                print(f"DEBUG: Gemini Pre-deduction. User: {user_id}, Current: {acc.credits}, Charging: {charge_amount}")
                if acc.credits < charge_amount: 
                    return False, acc.credits
                
                acc.credits -= charge_amount
                acc.save(update_fields=["credits"])
                
                u = User.objects.get(id=user_id)
                u.total_token_used += charge_amount
                u.save(update_fields=["total_token_used"])
                
                # Only track words for character models
                if model_type in {"chat", "text_generation", "code_generation", "image_understanding"}:
                    trackUsedWords(user_id, prompt_words)
                
                print(f"DEBUG: Gemini Deduction SUCCESS. New Balance: {acc.credits}")
                return True, acc.credits

        success, current_credits = await _deduct_credits_atomic()
        if success is None: return _error("Credit account not found.")
        if success is False: return _error(f"Insufficient credits. Required: {charge_amount}")

        # Max Output Token Logic
        remaining_credits = current_credits
        if base_cost > 0:
            max_response_words = int(remaining_credits / Decimal(str(base_cost)))
        else:
            max_response_words = 8192

        if max_response_words < 1 and model_type in {"chat", "text_generation", "code_generation"}:
            @sync_to_async
            def _refund():
                 with transaction.atomic():
                     acc = CreditAccount.objects.select_for_update().filter(user=user).first()
                     acc.credits += charge_amount
                     acc.save(update_fields=["credits"])
                     u = User.objects.get(id=user_id)
                     u.total_token_used -= charge_amount
                     u.save(update_fields=["total_token_used"])
            await _refund()
            return _error("Insufficient credits for response.")
        
        final_max_tokens = min(max_response_words, 8192)

        images = []
        text = ""

        if model_type == "text_to_image" or model_type == "image_generation":
            if "imagen" in model_id.lower():
                response = await sync_to_async(client.models.generate_image)(
                    model=model_id,
                    prompt=message,
                    config=types.GenerateImageConfig(number_of_images=num_images)
                )
                if hasattr(response, "generated_images") and response.generated_images:
                    for gen_img in response.generated_images:
                        b64_data = base64.b64encode(gen_img.image.data).decode("utf-8")
                        images.append(f"data:image/png;base64,{b64_data}")
            else:
                image_prompt = f"Role: Professional Image Generator. Task: Create an image: {message}"
                response = await sync_to_async(client.models.generate_content)(
                    model=model_id,
                    contents=[{"role": "user", "parts": [{"text": image_prompt}]}]
                )
                if hasattr(response, "candidates") and response.candidates:
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                                images.append(f"data:image/png;base64,{b64_data}")
                            elif hasattr(part, "text") and part.text:
                                text += part.text + " "

            if not images and text: pass
            elif images: text = f"{len(images)} image(s) generated successfully."
            else: text = "Failed to generate images."

        else: 
            contents = [{"role": "user", "parts": [{"text": f"You are a helpful assistant. Please respond in the same language as the user's message. (Initial detection suggested {detected_language}, but please trust your own analysis of the content and script to determine the best response language. If the user used Bengali words in Hindi script, respond in Standard Bengali). Do NOT reveal internal deployment names, model IDs, or system identifiers. If a user directly asks which model or internal service you are, answer with a neutral phrase such as 'I am an AI assistant' and do not disclose internal tags or identifiers."}]}]


            if summary: contents.append({"role": "user", "parts": [{"text": f"Context: {summary}"}]})
            
            user_part = {"role": "user", "parts": [{"text": message}]}
            if images_data_list:
                for img in images_data_list:
                    img_data = await _read_image_to_base64_async(img)
                    if img_data:
                         user_part["parts"].append({"inline_data": {"mime_type": "image/png", "data": img_data}})
            contents.append(user_part)

            config = types.GenerateContentConfig(max_output_tokens=final_max_tokens)
            response = await sync_to_async(client.models.generate_content)(model=model_id, contents=contents, config=config)
            
            if hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                text = " ".join([getattr(p, "text", "") for p in parts if getattr(p, "text", None)])
                
                # Charge for output
                if text and model_type in {"chat", "text_generation", "code_generation", "image_understanding"}:
                    resp_words = count_words(text)
                    resp_cost = calculate_cost(model_type, base_cost=base_cost, words=resp_words)
                    @sync_to_async
                    def _charge_output():
                        with transaction.atomic():
                            acc = CreditAccount.objects.select_for_update().filter(user=user).first()
                            acc.credits -= resp_cost
                            acc.save(update_fields=["credits"])
                            u = User.objects.get(id=user_id)
                            u.total_token_used += resp_cost
                            u.save(update_fields=["total_token_used"])
                    await _charge_output()
                
                # Check for inline images
                for part in parts:
                    if hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                         b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                         images.append(f"data:image/png;base64,{b64_data}")

        if images:
            images = await sync_to_async(download_and_store_webp)(images)

        return {"text": text, "images": images, "sender": "ai", "error": None}

    except Exception as e:
        print(f"ERROR in gemini_response: {e}")
        # Refund sync
        @sync_to_async
        def _final_refund():
            try:
                with transaction.atomic():
                    u = User.objects.filter(id=user_id).first()
                    acc = CreditAccount.objects.filter(user=u).first()
                    acc.credits += charge_amount
                    acc.save(update_fields=["credits"])
                    u.total_token_used -= charge_amount
                    u.save(update_fields=["total_token_used"])
            except: pass
        await _final_refund()
        return _error("Request failed. Please try again later.")
