# import os
# from celery import Celery
# from django.conf import settings

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIModelBackend.settings")

# app = Celery("AIModelBackend", broker=settings.CELERY_BROKER_URL)

# # Use Django settings for other configs
# app.config_from_object("django.conf:settings", namespace="CELERY")
# app.autodiscover_tasks()
# @app.task(bind=True)
# def debug_task(self):
#     print(f"Request: {self.request!r}") 