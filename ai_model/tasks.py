import os
import time
from celery import shared_task
from django.conf import settings

IMAGE_FOLDER = os.path.join(settings.BASE_DIR, "media/ai_images")
EXPIRATION_TIME =24 * 60 * 60  # 1 week in seconds

@shared_task
def delete_old_images():
    current_time = time.time()
    
    for filename in os.listdir(IMAGE_FOLDER):
        file_path = os.path.join(IMAGE_FOLDER, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > EXPIRATION_TIME:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
    return "Old images cleanup completed."