from django.contrib.auth import get_user_model
from google import genai
from accounts.models import CreditAccount  # adjust to your models
import requests, base64
from .track_used_word_subscription import trackUsedWords
from django.core.files.base import ContentFile
import base64

User = get_user_model()


User = get_user_model()


def gemini_response(
    message,
    model_id,
    api_key,
    user_id,
    images_data_list=None,
    summary=None,
    num_images=1,  # Always 1
    base_cost=500,  # Default base cost
):
    try:
        client = genai.Client(api_key=api_key)

        # -------------------------------
        # Fetch User + Credit Account
        # -------------------------------
        user = User.objects.filter(id=user_id).first()
        if not user:
            return _error("User not found.")

        credit_account = CreditAccount.objects.filter(user=user).first()
        if not credit_account:
            return _error("Credit account not found.")

        # -------------------------------
        # Image Generation (Gemini Lite supports only 1 image)
        # -------------------------------
        prompt_words = len(message.split())
        if credit_account.credits < prompt_words:
            return _error("Insufficient credits for prompt.")

        # Deduct prompt words
        credit_account.credits -= prompt_words
        credit_account.save()
        user.total_token_used += prompt_words
        user.save()
        trackUsedWords(user.id, prompt_words)
        is_image_generation = _is_image_generation_model(model_id)
        images = []

        if is_image_generation:
            num_images = 1
            base_cost = base_cost  # words
            total_cost = base_cost * num_images

            if credit_account.credits < total_cost:
                return _error(f"You don't have enough credits to generate {num_images} image(s).")

            # Deduct credits
            credit_account.credits -= total_cost
            credit_account.save()
            user.total_token_used += total_cost
            user.save()
            trackUsedWords(user.id, total_cost)
            message=f"create a image {message}"
            # Generate the image using generate_content
            response = client.models.generate_content(
                model=model_id,
                contents=[{"role": "user", "parts": [{"text": message}]}]
            )

            # Extract image from response
            # if hasattr(response, "candidates") and response.candidates:
            #     for part in response.candidates[0].content.parts:
            #         print("part",response.candidates[0].content.parts)
            #         if hasattr(part, "image") and hasattr(part.image, "data"):
            #             images.append(f"data:image/png;base64,{part.image.data}")
            if hasattr(response, "candidates") and response.candidates:
                 for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                    #    file_name = f"test_{user_id}.png"
                    #    with open(file_name, "wb") as f:
                    #          f.write(part.inline_data.data)
                       b64_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                       images.append(f"data:{part.inline_data.mime_type};base64,{b64_data}")
                       
            print("image URLs:", images)





            return {
                "text": f"{num_images} image(s) generated successfully.",
                "images": images,
                "sender": "ai",
                "error": None
            }

        # -------------------------------
        # Text / Image Understanding
        # -------------------------------


        # Build message content
        contents = []
        if summary:
            contents.append({
                "role": "user",
                "parts": [{"text": f"Conversation summary so far: {summary}"}]
            })

        contents.append({"role": "user", "parts": [{"text": message}]})

        # Add inline images if supported
        supports_image_input = _gemini_supports_image_input(model_id)
        if images_data_list and supports_image_input:
            user_index = 1 if summary else 0
            for img in images_data_list:
                img_data = _read_image_to_base64(img)
                if not img_data:
                    continue
                contents[user_index]["parts"].append({
                    "inline_data": {"mime_type": "image/png", "data": img_data}
                })

        # Generate text response
        response = client.models.generate_content(model=model_id, contents=contents)

        text = getattr(response, "text", "") or _extract_candidate_text(response)

        # Extract inline images
        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                    images.append(f"data:image/png;base64,{part.inline_data.data}")

        return {"text": text, "images": images, "sender": "ai", "error": None}

    except Exception as e:
        # Rollback credits if something goes wrong
        try:
            if 'credit_account' in locals():
                credit_account.credits += prompt_words
                user.total_token_used -= prompt_words
                credit_account.save()
        except:
            pass
        return _error(f"Gemini request failed: {str(e)}")


# ---------------------------
# Support functions
# ---------------------------

def _error(msg):
    return {"text": "", "images": [], "sender": "system", "error": msg}


def _is_image_generation_model(model_id):
    ml = model_id.lower()
    return any(x in ml for x in ["image", "img", "gen-img", "gemini-image", "photo", "art"])


def _gemini_supports_image_input(model_id):
    ml = model_id.lower()
    return not any(x in ml for x in ["lite", "tts", "audio", "embedding"])


def _extract_candidate_text(response):
    if hasattr(response, "candidates") and response.candidates:
        parts = response.candidates[0].content.parts
        return " ".join([getattr(p, "text", "") for p in parts if getattr(p, "text", None)])
    return ""


def _read_image_to_base64(img):
    try:
        if img.startswith("http"):
            resp = requests.get(img)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
        return img
    except:
        return None
