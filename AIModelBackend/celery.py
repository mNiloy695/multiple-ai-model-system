# myproject/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIModelBackend.settings')

app = Celery('AIModelBackend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'update-expired-subscriptions-every-midnight': {
        'task': 'plan.tasks.update_expired_subscriptions',
        'schedule': crontab(),  # Runs every day at 00:00 hour=0, minute=0
    },
}
