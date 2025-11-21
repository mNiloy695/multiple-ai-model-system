from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIModelBackend.settings')

# Create Celery app
app = Celery('AIModelBackend')

# Explicitly set Redis as broker and backend
app.conf.broker_url = "redis://127.0.0.1:6382/0"
app.conf.result_backend = "redis://127.0.0.1:6382/0"

# Optional: load additional config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from installed apps
app.autodiscover_tasks()

# Example beat schedule
app.conf.beat_schedule = {
    'update-expired-subscriptions-every-midnight': {
        'task': 'plan.tasks.update_expired_subscriptions',
        'schedule': crontab(hour=0, minute=0),
    },
}
