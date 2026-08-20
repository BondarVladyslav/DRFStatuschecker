import logging

logger = logging.getLogger(__name__)

from users.tasks import send_report_message


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
