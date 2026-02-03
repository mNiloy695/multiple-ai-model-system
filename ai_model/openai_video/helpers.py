import os
import uuid
from django.conf import settings
from django.utils.translation import gettext as _

def save_video(video_content, video_name=None):
 
    try:
        # Validate input
        if not video_content:
            return {
                "success": False,
                "error": _("Video content is empty")
            }
        
        if not isinstance(video_content, bytes):
            return {
                "success": False,
                "error": _("Video content must be bytes")
            }
        
        # Generate or use provided filename
        if not video_name:
            video_name = f"{uuid.uuid4()}.mp4"
        elif not video_name.endswith(".mp4"):
            video_name = f"{video_name}.mp4"
        
        save_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, video_name)
        
        
        if os.path.exists(file_path):
            base_name = video_name.replace(".mp4", "")
            video_name = f"{base_name}_{uuid.uuid4().hex[:8]}.mp4"
            file_path = os.path.join(save_dir, video_name)
       
        with open(file_path, "wb") as f:
            f.write(video_content)
        
  
        video_url = f"{settings.BASE_URL}{settings.MEDIA_URL}videos/{video_name}"
        
        return {
            "success": True,
            "filename": video_name,
            "filepath": file_path,
            "url": video_url,
        }
    
    except IOError as e:
        return {
            "success": False,
            "error": _("File write error: {}").format(str(e))
        }
    except Exception as e:
        return {
            "success": False,
            "error": _("Unexpected error saving video: {}").format(str(e))
        }
    
