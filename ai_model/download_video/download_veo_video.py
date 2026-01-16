import os, uuid, time
from django.conf import settings
from google import genai
from google.genai import types
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
User=get_user_model()
def video_generation_by_veo3(api_key, prompt, aspect_ratio, model_id, resolution,user_id,base_cost):
    client = genai.Client(api_key=api_key)

    if resolution not in ["720p", "1080p", "4k"]:
        resolution = "720p"
    
    if aspect_ratio not in ["9:16","16:9"]:
        aspect_ratio="9:16"

    saved_url=[]


    try:
        user=User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error":"No user Found"}
    
    try:
        user_account=user.creditaccount
        if user_account.credits<base_cost:
            raise ValueError("Insufficient credits to perform this operation.")
    except CreditAccount.DoesNotExist:
        return {"error":"Invalid user ID"}
    


    try:
        operation = client.models.generate_videos(
        model=model_id,
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        ),
    )
        video_url=download_and_store_video(api_key=api_key,operation_id=operation.id)
        saved_url.append(video_url)

    except Exception as e:
        print("video generating error for veo 3")
        saved_url.append(None)
        return {"error":f"AI error {e}"}
    return saved_url


def download_and_store_video(api_key, operation_id):
    client = genai.Client(api_key=api_key)

    # Wait for Veo to finish (with timeout)
    timeout = 300
    interval = 5
    elapsed = 0

    while elapsed < timeout:
        operation = client.operations.get(operation_id)
        if operation.done:
            break
        time.sleep(interval)
        elapsed += interval
    else:
        raise TimeoutError("Video generation timed out")

    generated_video = operation.response.generated_videos[0]

    # Prepare media directory
    save_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4()}.mp4"
    file_path = os.path.join(save_dir, filename)

    # Download video content
    import requests
    video_content = requests.get(generated_video.video).content
    with open(file_path, "wb") as f:
        f.write(video_content)

    # Return public URL
    return f"{settings.BASE_URL}{settings.MEDIA_URL}videos/{filename}"

