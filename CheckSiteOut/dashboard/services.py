import ipaddress
import logging
import socket

from django.db import transaction
from dashboard.exceptions import HostUnresolvable
from dashboard.tasks import site_check
from users.tasks import send_report_message
from .models import Site
from django_celery_beat.models import PeriodicTask, IntervalSchedule

logger = logging.getLogger(__name__)


@transaction.atomic
def add_site_for_user(*, link, user):
    site, created = Site.objects.get_or_create(link=link)
    site.owners.add(user)
    if created:
        transaction.on_commit(lambda: first_check_schedule(site.id, link))

    return site


def first_check_schedule(site_id, link):
    try:
        site_check.apply_async(args=(site_id, link), ignore_result=True)
    except Exception:
        logger.exception("Failed to schedule first check site: %s", site_id)
