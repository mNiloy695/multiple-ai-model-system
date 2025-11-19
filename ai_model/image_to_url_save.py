from django.http import HttpResponse, FileResponse
from django.conf import settings
from PIL import Image
import os
import io
import requests
from django.conf import settings
from PIL import Image
import io, os, uuid

def download_and_store_webp(image_urls):
    """
    Downloads a list of image URLs, converts each to WEBP,
    saves in MEDIA folder, and returns a list of saved media URLs.
    """
    saved_urls = []
    save_dir = os.path.join(settings.MEDIA_ROOT, "ai_images")
    os.makedirs(save_dir, exist_ok=True)

    for url in image_urls:
        try:
            response = requests.get(url)
            if response.status_code != 200:
                saved_urls.append(None)
                continue

            img = Image.open(io.BytesIO(response.content))
            file_name = f"{uuid.uuid4()}.webp"
            file_path = os.path.join(save_dir, file_name)

            # Save as WEBP
            img.save(file_path, "WEBP", quality=95)

            # Return media URL
            saved_urls.append(f"{settings.MEDIA_URL}ai_images/{file_name}")

        except Exception as e:
            print("Error processing URL:", url, e)
            saved_urls.append(None)

    return saved_urls
