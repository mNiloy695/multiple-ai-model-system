import os, uuid, asyncio, time, base64, requests
from pathlib import Path
from django.conf import settings
from google import genai
from google.genai import types
from django.contrib.auth import get_user_model
from accounts.models import CreditAccount
from asgiref.sync import sync_to_async
from django.utils.translation import gettext as _  
import django.db.transaction as transaction
User = get_user_model()

async def generate_veo3_preview_video(
    prompt: str,
    model_id: str,
    user_id,
    base_cost: float,
    api_key: str,
    resolution: str = "720p",
    aspect_ratio: str = "16:9"
) -> dict:
   
    try:
        if resolution not in ["720p", "1080p", "4k"]:
            resolution = "720p"
    
        if aspect_ratio not in ["9:16", "16:9"]:
            aspect_ratio = "9:16"

     
        user = await sync_to_async(lambda: User.objects.get(id=user_id))()
        user_account = await sync_to_async(lambda: user.creditaccount)()

        if user_account.credits < base_cost:
            raise ValueError(_("Insufficient credits"))

        
        client = genai.Client(api_key=api_key)

        config = types.GenerateVideosConfig(
            resolution=resolution,
            aspect_ratio=aspect_ratio,
        )
        model_id = "veo-3.1-generate-preview"

    
        operation = await sync_to_async(client.models.generate_videos)(
            model=model_id,
            prompt=prompt,
            config=config
        )

        
        max_wait_time = 300
        poll_interval = 10
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            
            operation = await sync_to_async(client.operations.get)(operation)
            if operation.done:
                break
            
            print(f"Waiting for Veo video... ({elapsed_time}s)")
            await asyncio.sleep(poll_interval) 
            elapsed_time += poll_interval

        if not operation.done:
            raise RuntimeError(_("Video generation timeout after {max_wait_time}s").format(max_wait_time=max_wait_time))

        if operation.error:
            raise RuntimeError(_("Video generation failed: {}").format(operation.error.message))

        generated_videos = operation.response.generated_videos
        if not generated_videos:
            raise RuntimeError(_("No videos generated"))

        video_data = generated_videos[0]
        video_bytes = None
        
        if hasattr(video_data.video, 'bytes_base64_encoded') and video_data.video.bytes_base64_encoded:
            video_bytes = base64.b64decode(video_data.video.bytes_base64_encoded)
        elif hasattr(video_data.video, 'uri') and video_data.video.uri:
            resp = await sync_to_async(requests.get)(video_data.video.uri, timeout=60)
            if resp.status_code == 200:
                video_bytes = resp.content

        if not video_bytes:
            raise RuntimeError(_("Failed to extract video bytes"))

        
        filename = f"{uuid.uuid4()}.mp4"
        video_dir = Path(settings.MEDIA_ROOT) / "videos"
        video_path = video_dir / filename
        
        def save_file():
            video_dir.mkdir(parents=True, exist_ok=True)
            with open(video_path, "wb") as f:
                f.write(video_bytes)
        
        await sync_to_async(save_file)()

        
        def final_deduct():
            with transaction.atomic():
                acc = CreditAccount.objects.select_for_update().filter(user_id=user_id).first()
                if acc:
                    print(f"DEBUG: [Veo3] Pre-deduction. User: {user_id}, Current: {acc.credits}, Charging: {base_cost}")
                    acc.credits -= Decimal(str(base_cost))
                    acc.save(update_fields=["credits"])
                    u = User.objects.get(id=user_id)
                    u.total_token_used += Decimal(str(base_cost))
                    u.save(update_fields=["total_token_used"])
                    print(f"DEBUG: [Veo3] Deduction SUCCESS. New Balance: {acc.credits}")
                else:
                    print(f"DEBUG: [Veo3] Credit account NOT FOUND for user_id {user_id}")
        
        await sync_to_async(final_deduct)()

        media_url = f"{settings.BASE_URL}{settings.MEDIA_URL}videos/{filename}"
        return {
            "text": _("Video generated successfully."),
            "images": [media_url],
            "type": "video"
        }

    except Exception as e:
        print(f"Veo-3 Error: {e}")
        raise RuntimeError(str(e))