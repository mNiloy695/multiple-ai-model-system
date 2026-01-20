from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from google import genai
from google.genai import types
from accounts.models import CreditAccount
from .track_used_word_subscription import trackUsedWords
import requests, base64
from .image_to_url_save import download_and_store_webp

User = get_user_model()

# =========================
# COST CALCULATION
# =========================
def calculate_cost(model_type, *, base_cost, words=0, num_images=1, input_images_count=0):
    base_cost = Decimal(str(base_cost))

    if model_type in {"chat", "text_generation", "code_generation", "image_understanding"}:
        # Charge for words + input images (flat fee per input image)
        return (Decimal(words) * base_cost) + (Decimal(input_images_count) * base_cost)

    if model_type == "image_generation":
        return Decimal(num_images) * base_cost
    
    return Decimal(base_cost)

# =========================
# HELPER: Detect Model Type
# =========================
def _detect_model_type(model_id):
    ml = model_id.lower()
    if any(x in ml for x in ["image", "img", "gen-img", "gemini-image", "photo", "art"]):
        return "image_generation"
    return "chat"

# =========================
# HELPER: Error Response
# =========================
def _error(msg):
    return {"text": "", "images": [], "sender": "system", "error": msg}

# =========================
# HELPER: Read Image
# =========================
def _read_image_to_base64(img):
    try:
        if img.startswith("http"):
            resp = requests.get(img)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
        return img
    except:
        return None

# =========================
# MAIN FUNCTION
# =========================
def gemini_response(
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
    resolution="720p"
):
    try:
        client = genai.Client(api_key=api_key)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return _error("User not found.")

        # Detect model type if not provided
        if not model_type:
            model_type = _detect_model_type(model_id)

        prompt_words = len(message.split())
        input_images_count = len(images_data_list) if images_data_list else 0
        
        charge_amount = calculate_cost(
            model_type,
            base_cost=base_cost,
            words=prompt_words,
            num_images=num_images,
            input_images_count=input_images_count
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
                return _error("Credit account not found.")

            if credit_account.credits < charge_amount:
                 return _error(f"Insufficient credits. Required: {charge_amount}")

            credit_account.credits -= charge_amount
            credit_account.save(update_fields=["credits"])

            user.total_token_used += charge_amount
            trackUsedWords(user.id, prompt_words)
            


            # --- CALCULATE REMAINING CREDITS FOR OUTPUT ---
            remaining_credits = credit_account.credits
            
            # Calculate how many words/tokens they can afford
            if base_cost > 0:
                max_response_words = int(remaining_credits / Decimal(str(base_cost)))
            else:
                max_response_words = 8192

            # If they can't afford any output, stop here
            if max_response_words < 1 and model_type in {"chat", "text_generation", "code_generation"}:
                 # Refund prompt
                 credit_account.credits += charge_amount
                 credit_account.save(update_fields=["credits"])
                 user.total_token_used -= charge_amount
                 user.save(update_fields=["total_token_used"])
                 return _error("Insufficient credits for response.")
            
            # Cap at safe limit (Gemini supports up to 8k or more depending on version)
            final_max_tokens = min(max_response_words, 8192)

        # =========================
        # MODEL EXECUTION
        # =========================
        
        images = []
        text = ""

        if model_type == "image_generation":
            # For Gemini Image Generation
            # Adjust prompt for image generation if needed
            image_prompt = f"create a image {message}"
            
            response = client.models.generate_content(
                model=model_id,
                contents=[{"role": "user", "parts": [{"text": image_prompt}]}]
            )
            
            # Extract image
            if hasattr(response, "candidates") and response.candidates:
                 for candidate in response.candidates:
                     if hasattr(candidate.content, "parts"):
                         for part in candidate.content.parts:
                            # Check for regular inline_data (common in gemini-1.5-flash)
                            if hasattr(part, "inline_data") and part.inline_data:
                               b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                               mime_type = part.inline_data.mime_type or "image/png"
                               images.append(f"data:{mime_type};base64,{b64_data}")
            
            # images conversion is now handled at the end
            text = f"{len(images)} image(s) generated successfully."

        else: 
            # Chat / Text / Image Understanding
            contents = []
            # Add a base system prompt for language and behavior
            contents.append({
                "role": "user", # Gemini uses 'user' role for system instructions in multi-turn
                "parts": [{"text": "You are a helpful assistant. Please respond in English by default, unless the user explicitly asks in another language or the context requires it."}]
            })

            if summary:
                contents.append({
                    "role": "user", # Gemini uses 'user' role for system instructions in multi-turn
                    "parts": [{"text": f"Conversation summary so far: {summary}. Do not show this summary in your response, use it for context."}]
                })

            # Add image generation behavior instruction as a separate context item
            contents.append({
                "role": "user",
                "parts": [{"text": "If you are not an image generation model but the user prompts you to generate an image, politely explain that you cannot generate images directly and suggest they use DALL-E 3 instead."}]
            })
            
            user_part = {"role": "user", "parts": [{"text": message}]}
            
            # Add images if present (Image Understanding)
            if images_data_list:
                # Gemini supports inline data in 'parts'
                for img in images_data_list:
                    img_data = _read_image_to_base64(img)
                    if img_data:
                         user_part["parts"].append({
                            "inline_data": {"mime_type": "image/png", "data": img_data}
                        })
            
            contents.append(user_part)

            # --- LIMIT OUTPUT TOKENS ---
            config = types.GenerateContentConfig(
                max_output_tokens=final_max_tokens
            )

            response = client.models.generate_content(
                model=model_id, 
                contents=contents,
                config=config 
            )
            
            # Extract text
            if hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                text = " ".join([getattr(p, "text", "") for p in parts if getattr(p, "text", None)])
            
            # --- CHARGE FOR OUTPUT TOKENS ---
            # Only charge for text/chat models. Image generation is pre-paid.
            if text and model_type in {"chat", "text_generation", "code_generation", "image_understanding"}:
                response_words = len(text.split())
                response_cost = calculate_cost( model_type, base_cost=base_cost, words=response_words)
                


                with transaction.atomic():
                    credit_account = CreditAccount.objects.select_for_update().filter(user=user).first()
                    if credit_account:
                        credit_account.credits -= response_cost
                        credit_account.save(update_fields=["credits"])
                        
                        user.total_token_used += response_cost
                        user.save(update_fields=["total_token_used"])
                        
                        trackUsedWords(user.id, response_words)



            # Extract inline images from response if any (Gemini sometimes returns images in chat)
            if hasattr(response, "candidates") and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                         b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                         images.append(f"data:image/png;base64,{b64_data}")

        # Convert simple Base64 images to stored URLs for ALL model types
        # This handles both explicit image_generation and chat models returning images (like Flash)
        if images:
            try:
                images = download_and_store_webp(images)
            except Exception:
                # Do NOT fail the request, just return empty images or whatever worked
                pass

        return {"text": text, "images": images, "sender": "ai", "error": None}

    except Exception as e:
        # =========================
        # EXACT REFUND (SAFE)
        # =========================
        error_str = str(e)
        print(f"ERROR in gemini_response: {error_str}")

        try:
            with transaction.atomic():
                refund_user = User.objects.filter(id=user_id).first()
                if refund_user:
                    refund_account = CreditAccount.objects.select_for_update().filter(user=refund_user).first()
                    if refund_account:
                        refund_account.credits += charge_amount
                        refund_account.save(update_fields=["credits"])
                        
                        refund_user.total_token_used -= charge_amount
                        refund_user.save(update_fields=["total_token_used"])

        except Exception:
            pass

        # Sanitize error message for user
        if "api_key" in error_str.lower() or "api key" in error_str.lower() or "key" in error_str.lower():
             return _error("Authentication failed: Invalid API key or configuration.")

        return _error(f"Request failed. Please try again later.")
