from venv import logger
from django.db import transaction
from users.tasks import send_report_message
from .models import Site
from django_celery_beat.models import PeriodicTask, IntervalSchedule


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
