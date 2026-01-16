import requests
from django.conf import settings
from PIL import Image
import io, os, uuid
import base64

def download_and_store_webp(image_urls):
    """
    Downloads a list of image URLs or base64 strings, converts each to PNG or JPEG,
    saves in MEDIA folder, and returns a list of saved media URLs.
    """
    saved_urls = []
    save_dir = os.path.join(settings.MEDIA_ROOT, "ai_images")
    os.makedirs(save_dir, exist_ok=True)

    for url in image_urls:
        try:
            # Handle Base64
            if url.startswith("data:image/"):
                header, encoded = url.split(",", 1)
                img_data = base64.b64decode(encoded)
                img_format = header.split("/")[1].split(";")[0].upper()
                if img_format not in ["PNG", "JPEG", "JPG"]:
                    img_format = "PNG"  # fallback

            # Handle normal URL
            elif url.startswith("http://") or url.startswith("https://"):
                response = requests.get(url, timeout=30)
                if response.status_code != 200:
                    saved_urls.append(None)
                    continue
                img_data = response.content
                img_format = response.headers.get("Content-Type", "image/png").split("/")[-1].upper()
                if img_format == "JPG":
                    img_format = "JPEG"
                elif img_format not in ["PNG", "JPEG"]:
                    img_format = "PNG"

            else:
                saved_urls.append(None)
                continue

            # Open image and convert
            img = Image.open(io.BytesIO(img_data))
            if img_format == "PNG":
                img = img.convert("RGBA")
                ext = "png"
            else:
                img = img.convert("RGB")
                ext = "jpg"

            # Save image
            file_name = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(save_dir, file_name)
            img.save(file_path, img_format, quality=95)

            saved_urls.append(f"{settings.BASE_URL}{settings.MEDIA_URL}ai_images/{file_name}")

        except Exception as e:
            print("Error processing URL/Base64:", url, e)
            saved_urls.append(None)

    return saved_urls


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
