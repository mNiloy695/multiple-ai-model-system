# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIModelBackend.settings")

app = Celery("AIModelBackend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# from celery.schedules import crontab
#not cancel is set past_due all subscriptions if current date is greater than current_period_end
# app.conf.beat_schedule = {
#     "auto-cancel-subscriptions-daily": {
#         "task": "plan.tasks.auto_cancel_expired_subscriptions",
#         "schedule": crontab(hour=0, minute=0),  # runs every day at midnight
#     },
# }

# from celery.schedules import crontab

# app.conf.beat_schedule = {
#     "auto-cancel-subscriptions-daily": {
#         "task": "plan.tasks.auto_cancel_expired_subscriptions",
#         "schedule": crontab(hour=0,minute=0),  # runs every day at midnight
#     },
# }