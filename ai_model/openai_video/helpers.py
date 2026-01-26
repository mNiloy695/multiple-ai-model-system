import os
import uuid
from django.conf import settings


def save_video(video_content, video_name=None):
    """
    Saves binary video content to Django MEDIA folder and returns accessible URL.
    
    Args:
        video_content (bytes): Binary video data from OpenAI API
        video_name (str, optional): Custom video filename. Defaults to UUID + .mp4
    
    Returns:
        dict: {
            "success": bool,
            "filename": str,
            "filepath": str,
            "url": str,
            "error": str (if failed)
        }
    
    Example:
        result = save_video(video_binary_data)
        if result["success"]:
            video_url = result["url"]
        else:
            print(result["error"])
    """
    try:
        # Validate input
        if not video_content:
            return {
                "success": False,
                "error": "Video content is empty"
            }
        
        if not isinstance(video_content, bytes):
            return {
                "success": False,
                "error": "Video content must be bytes"
            }
        
        # Generate or use provided filename
        if not video_name:
            video_name = f"{uuid.uuid4()}.mp4"
        elif not video_name.endswith(".mp4"):
            video_name = f"{video_name}.mp4"
        
        # Create videos directory
        save_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(save_dir, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(save_dir, video_name)
        
        # Check if file already exists (avoid overwriting)
        if os.path.exists(file_path):
            base_name = video_name.replace(".mp4", "")
            video_name = f"{base_name}_{uuid.uuid4().hex[:8]}.mp4"
            file_path = os.path.join(save_dir, video_name)
        
        # Write video to disk
        with open(file_path, "wb") as f:
            f.write(video_content)
        
        # Generate accessible URL
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
            "error": f"File write error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error saving video: {str(e)}"
        }
    
