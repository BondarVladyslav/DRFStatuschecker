
from users.models import Token
from datetime import timedelta
import time
from django.utils import timezone
import requests
from dashboard.models import Site, SiteResponse
from CheckSiteOut.celery import app
from users.services import send_report_message


@app.task(bind=True, max_retries=3)
def site_check(self, site_id, link):
    site = Site.objects.get(id=site_id) 
    last = SiteResponse.objects.filter(site_id=site_id).first()
    was_ok = last.error is None if last else True
    
    try:
        start = time.time()
        response = requests.head(link, timeout=10)   
        status_code = response.status_code
        response_obj = SiteResponse.objects.create(
            site_id=site_id,
            status_code=status_code,
            response_time=int((time.time()-start) * 1000),
        )
        if status_code >= 400:
            error = f'Bad status code {status_code}'

            if was_ok:
                alert_all_owners(error, site.owners.all(), link)

            response_obj.error = error
            response_obj.save()
            

        else:
            response_obj.save()
    except requests.exceptions.RequestException as error:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=error, countdown=10)
        else:
            error = 'TIMEOUT' if isinstance(error, requests.exceptions.Timeout) else 'CONNECTION_FAILED'
            SiteResponse.objects.create(site_id=site_id, error=error)
            if was_ok:
                alert_all_owners(error, site.owners.all(), link)
@app.task
def cleanup_tokens():
    Token.objects.filter(
        created_at__lt=timezone.now() - timedelta(hours=1)
    ).delete()


def alert_all_owners(error, owners, link):
    for owner in owners:
        send_report_message(telegram_id=owner.username.removeprefix('tg_'), text=f'''Your site {link} responsed an error {error}''')
