import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CheckSiteOut.settings')

app = Celery('site_checker')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'cleanup-tokens': {
        'task': 'dashboard.tasks.cleanup_tokens',
        'schedule': crontab(minute=0), 
    },
}