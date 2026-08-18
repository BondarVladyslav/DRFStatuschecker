import ipaddress
import logging
import socket
from urllib.parse import urlsplit

from .services import check_ip_blocked
from dashboard.services import alert_all_owners
from users.models import Token
from datetime import timedelta
import time
import requests
from dashboard.models import Site, SiteResponse
from CheckSiteOut.celery import app
from users.tasks import send_report_message
from django.utils import timezone

logger = logging.getLogger(__name__)


@app.task(bind=True)
def send_site_checking_task(self):
    sites = Site.objects.filter(checked_at__lt=timezone.now() - timedelta(minutes=1))

    for site in sites:
        site_check.delay(site.id, site.link)


@app.task(bind=True, max_retries=3)
def site_check(self, site_id, link):
    response = None
    site = Site.objects.get(id=site_id)
    last = SiteResponse.objects.filter(site_id=site_id).first()
    was_ok = not (last and last.error)

    try:
        if check_ip_blocked(urlsplit(link).hostname):
            SiteResponse.objects.create(site_id=site_id, error="BLOCKED_HOST")
            return

        start = time.time()
        response = requests.head(link, timeout=10)
        status_code = response.status_code
        if status_code in (403, 405, 501):
            start = time.time()
            response = requests.get(link, timeout=10, allow_redirects=False)
            status_code = response.status_code
        response_obj = SiteResponse.objects.create(
            site_id=site_id,
            status_code=status_code,
            response_time=int((time.time() - start) * 1000),
        )
        if status_code >= 400:
            error = f"Bad status code {status_code}"

            if was_ok:
                alert_all_owners(
                    site.owners.all(), link, became_avaible=False, error=error
                )

            response_obj.error = error
            response_obj.save()

        else:
            if not was_ok:
                alert_all_owners(site.owners.all(), link, became_avaible=True)
            response_obj.save()

    except requests.exceptions.RequestException as error:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=error, countdown=10)
        else:
            error = (
                "TIMEOUT"
                if isinstance(error, requests.exceptions.Timeout)
                else "CONNECTION_FAILED"
            )
            SiteResponse.objects.create(site_id=site_id, error=error)
            if was_ok:
                alert_all_owners(
                    site.owners.all(), link, became_avaible=False, error=error
                )
    finally:
        if self.request.retries == self.max_retries or (
            response is not None and response.status_code < 400
        ):
            site.checked_at = timezone.now()
            site.save()


@app.task
def cleanup_history():
    SiteResponse.objects.filter(
        checked_at__lt=timezone.now() - timedelta(weeks=2)
    ).delete()
