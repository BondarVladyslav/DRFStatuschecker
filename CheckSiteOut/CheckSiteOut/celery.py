import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CheckSiteOut.settings")

app = Celery("site_checker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "cleanup-tokens": {
        "task": "users.tasks.cleanup_tokens",
        "schedule": crontab(minute=0),
    },
    "send_site_checking_task": {
        "task": "dashboard.tasks.send_site_checking_task",
        "schedule": crontab(minute="*"),
    },
    "cleanup_history": {
        "task": "dashboard.tasks.cleanup_history",
        "schedule": crontab(hour=0, minute=0),
    },
}
