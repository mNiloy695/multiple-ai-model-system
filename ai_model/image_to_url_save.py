import requests
from django.conf import settings
from PIL import Image
import io, os, uuid
import base64

def download_and_store_webp(image_urls):
    """
    Downloads a list of image URLs or base64 strings, converts each to PNG, JPEG, WEBP or SVG,
    saves in MEDIA folder, and returns a list of saved media URLs.
    """
    if isinstance(image_urls, str):
        image_urls = [image_urls]
        
    saved_urls = []
    save_dir = os.path.join(settings.MEDIA_ROOT, "ai_images")
    os.makedirs(save_dir, exist_ok=True)

    for url in image_urls:
        if not url:
            saved_urls.append(None)
            continue
            
        try:
            img_data = None
            img_format = None
            ext = None

            # Handle Base64
            if url.startswith("data:") or (len(url) > 100 and ("," in url or "base64" in url.lower())):
                header = ""
                encoded = url
                if "," in url:
                    header, encoded = url.split(",", 1)
                
                # Check for padding issues in base64
                missing_padding = len(encoded) % 4
                if missing_padding:
                    encoded += "=" * (4 - missing_padding)
                
                img_data = base64.b64decode(encoded)
                header_lower = header.lower()
                
                if "svg" in header_lower:
                    img_format = "SVG"
                elif "webp" in header_lower:
                    img_format = "WEBP"
                elif "jpeg" in header_lower or "jpg" in header_lower:
                    img_format = "JPEG"
                elif "png" in header_lower:
                    img_format = "PNG"
                else:
                    # Try to detect via PIL if header is missing/generic
                    try:
                        temp_img = Image.open(io.BytesIO(img_data))
                        img_format = temp_img.format
                    except:
                        img_format = "PNG" # Default fallback
            
            # Handle normal URL
            elif url.startswith("http://") or url.startswith("https://"):
                # Detect if URL is already local to avoid loopback errors
                is_local = any(x in url for x in ["127.0.0.1", "localhost", "0.0.0.0"])
                if settings.BASE_URL and settings.BASE_URL in url:
                    is_local = True
                
                if is_local and ("/media/" in url):
                    saved_urls.append(url)
                    continue

                response = requests.get(url, timeout=30)
                if response.status_code != 200:
                    saved_urls.append(None)
                    continue
                img_data = response.content
                content_type = response.headers.get("Content-Type", "").lower()
                
                if "svg" in content_type:
                    img_format = "SVG"
                elif "webp" in content_type:
                    img_format = "WEBP"
                elif "png" in content_type:
                    img_format = "PNG"
                elif "jpeg" in content_type or "jpg" in content_type:
                    img_format = "JPEG"
                else:
                    try:
                        temp_img = Image.open(io.BytesIO(img_data))
                        img_format = temp_img.format
                    except:
                        img_format = "PNG"

            else:
                # Might be raw base64 without any indicator
                try:
                    missing_padding = len(url) % 4
                    encoded = url + ("=" * (4 - missing_padding)) if missing_padding else url
                    img_data = base64.b64decode(encoded)
                    temp_img = Image.open(io.BytesIO(img_data))
                    img_format = temp_img.format
                except:
                    saved_urls.append(None)
                    continue

            if not img_data:
                saved_urls.append(None)
                continue

            # Process SVG (binary save)
            if img_format == "SVG":
                file_name = f"{uuid.uuid4()}.svg"
                file_path = os.path.join(save_dir, file_name)
                with open(file_path, "wb") as f:
                    f.write(img_data)
                saved_urls.append(f"{settings.BASE_URL}{settings.MEDIA_URL}ai_images/{file_name}")
                continue

            # Process with PIL for other formats
            img = Image.open(io.BytesIO(img_data))
            
            # Extension and mode logic
            if img_format in ["PNG", "WEBP"]:
                img = img.convert("RGBA")
                ext = img_format.lower()
            else:
                img = img.convert("RGB")
                ext = "jpg"
                img_format = "JPEG"

            file_name = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(save_dir, file_name)
            img.save(file_path, img_format, quality=95)

            saved_urls.append(f"{settings.BASE_URL}{settings.MEDIA_URL}ai_images/{file_name}")

        except Exception as e:
            print(f"Error processing URL/Base64 in download_and_store_webp: {e}")
            saved_urls.append(None)

    return saved_urls


def download_and_store_video(video_urls):
    """
    Downloads a list of video URLs, saves in MEDIA/videos folder,
    and returns a list of saved media URLs.
    """
    if isinstance(video_urls, str):
        video_urls = [video_urls]
        
    saved_urls = []
    save_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(save_dir, exist_ok=True)

    for url in video_urls:
        if not url:
            saved_urls.append(None)
            continue
            
        try:
            if url.startswith("http://") or url.startswith("https://"):
                # Detect if URL is already local to avoid loopback errors
                is_local = any(x in url for x in ["127.0.0.1", "localhost", "0.0.0.0"])
                if settings.BASE_URL and settings.BASE_URL in url:
                    is_local = True

                if is_local and ("/media/" in url):
                    saved_urls.append(url)
                    continue
                    
                response = requests.get(url, timeout=120)  # Video can be large
                if response.status_code != 200:
                    saved_urls.append(None)
                    continue
                video_data = response.content
            else:
                saved_urls.append(None)
                continue

            # Save video
            file_name = f"{uuid.uuid4()}.mp4"
            file_path = os.path.join(save_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(video_data)

            saved_urls.append(f"{settings.BASE_URL}{settings.MEDIA_URL}videos/{file_name}")

        except Exception as e:
            print("Error processing video URL:", url, e)
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

# -----------------------------
# Audio download & save helper
# -----------------------------
def download_and_store_audio(audio_data):
    """
    Downloads/Decodes audio data (URL or Base64), saves in MEDIA/audio folder,
    and returns the local media URL.
    Returns string path or None.
    """
    if not audio_data:
        return None

    save_dir = os.path.join(settings.MEDIA_ROOT, "voice_chat")
    os.makedirs(save_dir, exist_ok=True)
    
    saved_url = None
    
    try:
        final_data = None
        ext = "mp3" 

        # A. Handle URL
        if isinstance(audio_data, str) and audio_data.startswith("http"):
            print(f"DEBUG: Processing audio URL: {audio_data}")
            if "/media/" in audio_data:
                rel_path = audio_data.split('/media/')[-1]
                return {"full_url": audio_data, "relative_path": rel_path}

            # Add comprehensive browser-like headers to bypass Cloudflare/Bot protection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,audio/mpeg,audio/*;q=0.8,*/*;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://file-examples.com/',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            response = requests.get(audio_data, headers=headers, timeout=30)
            if response.status_code == 200:
                final_data = response.content
                # Try to guess extension
                content_type = response.headers.get('Content-Type', '').lower()
                if 'wav' in content_type: ext = 'wav'
                elif 'ogg' in content_type: ext = 'ogg'
            else:
                print(f"DEBUG: URL download failed. Status: {response.status_code} for {audio_data}")
                if response.status_code == 403:
                    print("DEBUG: Site blocked the request (Cloudflare/Bot protection detected).")

        # B. Handle Base64
        elif isinstance(audio_data, str) and (";base64," in audio_data or len(audio_data) > 500):
            print("DEBUG: Processing Base64 audio data")
            header, encoded = (audio_data.split(",", 1) if "," in audio_data else ("", audio_data))
            if "wav" in header.lower(): ext = "wav"
            elif "ogg" in header.lower(): ext = "ogg"
            missing_padding = len(encoded) % 4
            if missing_padding: encoded += "=" * (4 - missing_padding)
            final_data = base64.b64decode(encoded)

        # C. Handle Raw Bytes
        elif isinstance(audio_data, bytes):
            final_data = audio_data

        if final_data:
            file_name = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(save_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(final_data)
            
            relative_path = f"voice_chat/{file_name}"
            # Ensure URL is built cleanly
            base_url = settings.BASE_URL.rstrip('/')
            media_url = settings.MEDIA_URL.strip('/')
            full_url = f"{base_url}/{media_url}/{relative_path}"
            return {"full_url": full_url, "relative_path": relative_path}

    except Exception as e:
        print(f"Error processing audio data: {e}")
        return None

    return None
