import requests
from django.conf import settings
from PIL import Image
import io, os, uuid

# def download_and_store_webp(image_urls):
#     """
#     Downloads a list of image URLs, converts each to WEBP,
#     saves in MEDIA folder, and returns a list of saved media URLs.
#     """
#     saved_urls = []
#     save_dir = os.path.join(settings.MEDIA_ROOT, "ai_images")
#     os.makedirs(save_dir, exist_ok=True)

#     for url in image_urls:
#         try:
#             response = requests.get(url)
#             if response.status_code != 200:
#                 saved_urls.append(None)
#                 continue

#             img = Image.open(io.BytesIO(response.content))
#             file_name = f"{uuid.uuid4()}.webp"
#             file_path = os.path.join(save_dir, file_name)

#             # Save as WEBP
#             img.save(file_path, "WEBP", quality=95)

#             # Return media URL
#             #  full_url = f"{settings.BASE_URL}{settings.MEDIA_URL}ai_images/{file_name}"
#             saved_urls.append(f"{settings.BASE_URL}{settings.MEDIA_URL}ai_images/{file_name}")

#         except Exception as e:
#             print("Error processing URL:", url, e)
#             saved_urls.append(None)

#     return saved_urls
import base64
import os
import io
import uuid
import base64
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from openai import OpenAI
from .track_used_word_subscription import trackUsedWords

User = get_user_model()
MODEL_CACHE = {}

# -----------------------------
# Image download & save helper
# -----------------------------
def download_and_store_webp(image_urls):
    
    """
    Accepts a list of base64 strings or image URLs.
    Converts base64 images to WEBP and returns a list of URLs.
    If item is already a URL, just return it as is.
    """
    
    saved_urls = []
    save_dir = os.path.join(settings.MEDIA_ROOT, "ai_images")
    os.makedirs(save_dir, exist_ok=True)

    for img_data in (image_urls):
        try: 
            if img_data.startswith("http") or img_data.startswith("https"):
                # Already a URL
                saved_urls.append(img_data)
                continue

            # Remove prefix if exists
            if "," in img_data:
                _, img_data = img_data.split(",", 1)

            # Decode base64 and save
            image_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(image_bytes))
            file_name = f"{uuid.uuid4()}.webp"
            file_path = os.path.join(save_dir, file_name)
            img.save(file_path, "WEBP", quality=95)
            saved_urls.append(f"{settings.BASE_URL}{settings.MEDIA_URL}ai_images/{file_name}")

        except Exception as e:
            print("Error processing image:", e)
            saved_urls.append(None)

    return saved_urls
