import os, uuid, time
from django.conf import settings
from google import genai
from google.genai import types
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
User=get_user_model()
# def video_generation_by_veo3(api_key, prompt, aspect_ratio, model_id, resolution,user_id,base_cost):
#     client = genai.Client(api_key=api_key)

#     if resolution not in ["720p", "1080p", "4k"]:
#         resolution = "720p"
    
#     if aspect_ratio not in ["9:16","16:9"]:
#         aspect_ratio="9:16"

#     saved_url=[]


#     try:
#         user=User.objects.get(id=user_id)
#     except User.DoesNotExist:
#         return {"error":"No user Found"}
    
#     try:
#         user_account=user.creditaccount
#         if user_account.credits<base_cost:
#             raise ValueError("Insufficient credits to perform this operation.")
#     except CreditAccount.DoesNotExist:
#         return {"error":"Invalid user ID"}
    


#     try:
#         operation = client.models.generate_videos(
#         model=model_id,
#         prompt=prompt,
#         config=types.GenerateVideosConfig(
#             aspect_ratio=aspect_ratio,
#             resolution=resolution,
#         ),
#     )
#         video_url=download_and_store_video(api_key=api_key,operation_id=operation.id)
#         saved_url.append(video_url)

#     except Exception as e:
#         print("video generating error for veo 3")
#         saved_url.append(None)
#         return {"error":f"AI error {e}"}
#     return saved_url


# def download_and_store_video(api_key, operation_id):
#     client = genai.Client(api_key=api_key)

#     # Wait for Veo to finish (with timeout)
#     timeout = 300
#     interval = 5
#     elapsed = 0

#     while elapsed < timeout:
#         operation = client.operations.get(operation_id)
#         if operation.done:
#             break
#         time.sleep(interval)
#         elapsed += interval
#     else:
#         raise TimeoutError("Video generation timed out")

#     generated_video = operation.response.generated_videos[0]

#     # Prepare media directory
#     save_dir = os.path.join(settings.MEDIA_ROOT, "videos")
#     os.makedirs(save_dir, exist_ok=True)

#     filename = f"{uuid.uuid4()}.mp4"
#     file_path = os.path.join(save_dir, filename)

#     # Download video content
#     import requests
#     video_content = requests.get(generated_video.video).content
#     with open(file_path, "wb") as f:
#         f.write(video_content)

#     # Return public URL
#     return f"{settings.BASE_URL}{settings.MEDIA_URL}videos/{filename}"

import base64
import uuid
from pathlib import Path
from google import genai
from google.genai import types
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


import time
import base64
import uuid
from pathlib import Path
from google import genai
from google.genai import types
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_veo3_preview_video(
    prompt: str,
    model_id: str,
    user_id,
    base_cost: float,
    api_key: str,
    resolution: str = "720p",
    aspect_ratio: str = "16:9"
) -> str:
    """
    Generate a preview video using Google's Veo-3 model with long-running operations.
    
    Args:
        prompt: Video description
        model_id: Model identifier (e.g., "veo-3.1-generate-preview")
        user_id: User ID
        base_cost: Credit cost
        api_key: Google API key
        resolution: Video resolution (default "720p")
        aspect_ratio: Video aspect ratio (default "16:9")
        
    Returns:
        str: Media URL path to the generated video
        
    Raises:
        ValueError: If insufficient credits
        RuntimeError: If video generation fails
    """
    try:
        # Get user and validate credits
        if resolution not in ["720p", "1080p", "4k"]:
            resolution = "720p"
    
        if aspect_ratio not in ["9:16","16:9"]:
            aspect_ratio="9:16"
        user = User.objects.get(id=user_id)
        user_account = user.creditaccount

        if user_account.credits < base_cost:
            raise ValueError("Insufficient credits")

        # Initialize Google GenAI client
        client = genai.Client(api_key=api_key)

        # ✅ FIX: Create config with resolution and aspect ratio
        config = types.GenerateVideosConfig(
            resolution=resolution,
            aspect_ratio=aspect_ratio,
        )
        model_id="veo-3.1-generate-preview"

        # ✅ FIX: Start long-running video generation operation
        operation = client.models.generate_videos(
            model=model_id,  # Use "veo-3.1-generate-preview" or "veo-3.0-generate-preview"
            prompt=prompt,
            config=config
        )

        # ✅ FIX: Poll the operation until completion
        max_wait_time = 300  # 5 minutes max wait
        poll_interval = 10   # Check every 10 seconds
        elapsed_time = 0

        while not operation.done and elapsed_time < max_wait_time:
            print(f"Waiting for video generation... ({elapsed_time}s)")
            time.sleep(poll_interval)
            elapsed_time += poll_interval
            
            # Get updated operation status
            operation = client.operations.get(operation)

        if not operation.done:
            raise RuntimeError(f"Video generation timeout after {max_wait_time}s")

        # ✅ FIX: Check for errors in operation
        if operation.error:
            raise RuntimeError(f"Video generation failed: {operation.error.message}")

        # ✅ FIX: Access the response correctly
        if not operation.response or not hasattr(operation.response, 'generated_videos'):
            raise RuntimeError("No video data in response")

        generated_videos = operation.response.generated_videos
        if not generated_videos or len(generated_videos) == 0:
            raise RuntimeError("No videos generated")

        # Get first video
        video_data = generated_videos[0]

        # ✅ FIX: Extract video bytes correctly
        video_bytes = None
        
        # Check if video is base64 encoded
        if hasattr(video_data.video, 'bytes_base64_encoded'):
            video_bytes = base64.b64decode(video_data.video.bytes_base64_encoded)
        # Check if video is stored in GCS
        elif hasattr(video_data.video, 'gcs_uri'):
            # If using GCS, download from the URI
            gcs_uri = video_data.video.gcs_uri
            print(f"Video stored in GCS: {gcs_uri}")
            # You would need to download from GCS here
            raise RuntimeError("GCS storage not implemented. Use base64 encoding instead.")
        else:
            raise RuntimeError("Unsupported video storage format")

        if not video_bytes:
            raise RuntimeError("Failed to extract video bytes")

        # ✅ FIX: Save video to disk
        filename = f"{uuid.uuid4()}.mp4"
        video_dir = Path(settings.MEDIA_ROOT) / "videos"
        video_path = video_dir / filename

        video_dir.mkdir(parents=True, exist_ok=True)

        with open(video_path, "wb") as f:
            f.write(video_bytes)

        # ✅ FIX: Deduct credits only after successful generation
        user_account.credits -= base_cost
        user_account.save()

        print(f"Video saved successfully: {video_path}")

        # Return media URL
        media_url = f"{settings.MEDIA_URL}videos/{filename}"
        return media_url

    except ValueError as ve:
        # Re-raise ValueError with original message (credit issues)
        print(f"Validation error: {ve}")
        raise ve
        
    except Exception as e:
        # Log the actual error for debugging
        print(f"Veo-3 generation failed: {type(e).__name__}: {e}")
        raise RuntimeError(f"Video generation failed: {str(e)}") from e