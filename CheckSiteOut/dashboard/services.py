import json

from django.db import transaction

from .tasks import site_check
from .models import Site, SiteResponse
from .serializers import SiteResponseSerializer
from django_celery_beat.models import PeriodicTask, IntervalSchedule

import time
import requests
from CheckSiteOut.celery import app
from .models import Site, SiteResponse


@transaction.atomic
def add_site_for_user(*, link, user):
    site, created = Site.objects.get_or_create(link=link)
    site.owners.add(user)
    if created:
        transaction.on_commit(lambda: site_check.delay(site.id, link))

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        PeriodicTask.objects.get_or_create(
            name=f'check_site_{site.id}',
            defaults={
                'interval': schedule,
                'task': 'dashboard.tasks.site_check',
                'args': json.dumps([site.id, link]),
            }
        )
    return site


def stop_monitoring(site_id):
    task = PeriodicTask.objects.filter(
        name=f'check_site_{site_id}'
    )
    task.delete()

def normalize_link(link):
    return link if link.startswith(('http://', 'https://')) else 'https://' + link