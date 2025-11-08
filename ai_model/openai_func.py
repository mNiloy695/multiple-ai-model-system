from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from openai import OpenAI
import base64

User = get_user_model()

def gpt_response(
    message: str,
    model_id: str,
    api_key: str,
    user_id: int,
    images_data_list: list[str] | None = None,
    width=None,
    height=None,
    audio_data: str | None = None,
    max_response_tokens: int = 1000,
) -> dict:
 

    try:
        client = OpenAI(api_key=api_key)

      
        user = User.objects.filter(id=user_id).first()
        if not user:
            return _error("User not found.")

        credit_account = CreditAccount.objects.filter(user=user).first()
        if not credit_account:
            return _error("Credit account not found.")

       
        prompt_words = len(message.split())
        if credit_account.credits < prompt_words:
            return _error("Insufficient credits for prompt.")

        credit_account.credits -= prompt_words
        credit_account.save()

        model_lower = model_id.lower()
        model_type = _detect_model_type(model_lower, images_data_list, audio_data)

        text, images = "", []

        
        if model_type == "chat":
            text = _chat_request(client, model_id, message, max_response_tokens)

        elif model_type == "completion":
            text = _completion_request(client, model_id, message, max_response_tokens)

        elif model_type == "image_understanding":
            text = _vision_request(client, model_id, message, images_data_list, max_response_tokens)

        elif model_type == "image_generation":
            text, images = _image_request(client, model_id, message,width,
    height)

        elif model_type == "audio_generation":
            text = _audio_request(client, model_id, message, audio_data)

        elif model_type == "embedding":
            text = _embedding_request(client, model_id, message)

        elif model_type == "moderation":
            text = _moderation_request(client, model_id, message)

        else:
            return _error(f"Unsupported model type for '{model_id}'.")

        response_words = len(text.split())
        if response_words > credit_account.credits:
            allowed = credit_account.credits
            text = " ".join(text.split()[:allowed])
            response_words = allowed

        credit_account.credits -= response_words
        credit_account.save()

        return {"text": text, "images": images, "sender": "ai", "error": None}

    except Exception as e:

        try:
            if 'credit_account' in locals():
                credit_account.credits += prompt_words
                credit_account.save()
        except Exception:
            pass

    
        error_message = str(e)
        if "billing_hard_limit_reached" in error_message:
            error_message = "OpenAI billing limit reached for this account."
        elif "not allowed to sample" in error_message:
            error_message = "Selected model not available or unauthorized."
        elif "insufficient_quota" in error_message:
            error_message = "Your OpenAI quota has been exceeded."

        return _error(f"GPT request failed: {error_message}")




def _error(msg: str) -> dict:
    return {"text": "", "images": [], "sender": "system", "error": msg}


def _detect_model_type(model_lower: str, images_data_list: list | None, audio_data: str | None) -> str:
    """Detects the type of OpenAI model dynamically."""
    if any(k in model_lower for k in ["dall-e", "image-gen", "image_generate", "gpt-image"]):
        return "image_generation"
    if images_data_list and any(k in model_lower for k in ["vision", "gpt-4o", "gpt-4-vision"]):
        return "image_understanding"
    if audio_data and any(k in model_lower for k in ["tts", "audio", "gpt-audio"]):
        return "audio_generation"
    if any(k in model_lower for k in ["embedding", "text-embedding"]):
        return "embedding"
    if any(k in model_lower for k in ["moderation", "omni-moderation"]):
        return "moderation"
    if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
        return "chat"
    if any(k in model_lower for k in ["davinci", "curie", "babbage", "ada"]):
        return "completion"
    return "unknown"


def _chat_request(client, model_id, message, max_tokens):
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": message}],
        max_completion_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def _completion_request(client, model_id, message, max_tokens):
    response = client.completions.create(
        model=model_id,
        prompt=message,
        max_completion_tokens=max_tokens
    )
    return response.choices[0].text.strip()


def _vision_request(client, model_id, message, images_data_list, max_tokens):
    image_blocks = []
    for img in images_data_list or []:
        if img.startswith("http"):
            image_blocks.append({"type": "image_url", "image_url": img})
        else:
            image_blocks.append({"type": "image_url", "image_url": f"data:image/png;base64,{img}"})

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": message}] + image_blocks}
        ],
        max_completion_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def _image_request(client, model_id, prompt, width=None, height=None):
    """
    Generate an image using any OpenAI image model.
    """
    # Default size
    size = f"{width}x{height}" if width and height else "1024x1024"

    # Optionally: define some common allowed sizes
    common_sizes = {"256x256", "512x512", "1024x1024", "1024x1792", "1792x1024", "2048x2048"}
    if size not in common_sizes:
        size = "1024x1024"  # fallback

    # Generate image dynamically using any model
    response = client.images.generate(
        model=model_id,
        prompt=prompt,
        size=size
    )

    images = [img.url for img in response.data]
    return f"Image generated successfully ({size}) using {model_id}.", images




def _audio_request(client, model_id, message, audio_data):
    """Generate or process audio (TTS/voice)."""
    if not audio_data:
        raise Exception("Audio data required for this model.")
    response = client.audio.transcriptions.create(
        model=model_id,
        file=audio_data
    )
    return response.text.strip()


def _embedding_request(client, model_id, message):
    response = client.embeddings.create(
        model=model_id,
        input=message
    )
    return str(response.data[0].embedding)


def _moderation_request(client, model_id, message):
    response = client.moderations.create(
        model=model_id,
        input=message
    )
    return str(response.results[0])


