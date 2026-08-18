import ipaddress
import logging
import socket

from django.db import transaction
from users.tasks import send_report_message
from .models import Site
from django_celery_beat.models import PeriodicTask, IntervalSchedule

logger = logging.getLogger(__name__)


@transaction.atomic
def add_site_for_user(*, link, user):
    from .tasks import site_check

    site, created = Site.objects.get_or_create(link=link)
    site.owners.add(user)
    if created:
        transaction.on_commit(lambda: site_check.delay(site.id, link))

    return site


def alert_all_owners(owners, link, became_avaible, error=None):
    message = (
        f"""Your site {link} became available"""
        if became_avaible
        else f"""Your site {link} responded an error {error}"""
    )
    for owner in owners:
        try:
            send_report_message.delay(
                telegram_id=owner.telegram_id,
                text=message,
            )
        except Exception:
            logger.exception("Failed sending task for alert for owner %s", owner.id)


def check_ip_blocked(host):
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return True
    return False
