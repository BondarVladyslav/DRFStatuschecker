from unittest.mock import MagicMock, patch
from celery.exceptions import Retry

import pytest
import requests

from dashboard.models import SiteResponse
from dashboard.tasks import site_check

def response_factory(status_code):
    response = MagicMock()
    response.status_code = status_code
    return response

def test_saving_successful_response(site):
    with patch('dashboard.tasks.requests.head',
               return_value = response_factory(200)) as resp_mock:
        with patch('dashboard.tasks.alert_all_owners') as alert_mock:

            site_check.apply(args = [site.id, site.link])
            resp_mock.assert_called_once_with(site.link, timeout = 10)
            obj = SiteResponse.objects.get()
            assert obj.status_code == 200
            assert obj.error == None
            assert obj.response_time >=0
            alert_mock.assert_not_called()

class TestCheckWithBadStatus:
    def test_500_creates_error_and_alerts(self,site,user):
        with patch('dashboard.tasks.requests.head',
               return_value = response_factory(500)) as resp_mock:

            with patch('dashboard.tasks.alert_all_owners') as alert_mock:

                site_check.apply(args=[site.id, site.link])

        obj = SiteResponse.objects.get()
        assert obj.status_code == 500
        assert obj.error == 'Bad status code 500'
        alert_mock.assert_called_once()

    def test_dont_repeat_alert_when_was_down(self,site,make_response):
        make_response(
            status_code = 500,
            error = 'Bad status code 500'
                      )
        
        with patch('dashboard.tasks.requests.head',
            return_value = response_factory(500)) as resp_mock:

            with patch('dashboard.tasks.alert_all_owners') as alert_mock:

                site_check.apply(args=[site.id, site.link])

            alert_mock.assert_not_called()


    def test_alert_after_recovery(self, site, make_response):
        make_response(
            status_code = 500,
            error='Bad status code 500'
        )
        make_response(
                    status_code = 200,
                    error=None
                )
        with patch('dashboard.tasks.requests.head',
            return_value = response_factory(500)) as resp_mock:

            with patch('dashboard.tasks.alert_all_owners') as alert_mock:

                site_check.apply(args=[site.id, site.link])

            alert_mock.assert_called_once()



class TestSiteNetworkErrors:
    def test_error_triggers_retry(self, site):
        with patch('dashboard.tasks.requests.head', side_effect=requests.exceptions.ConnectionError()):
            with patch('dashboard.tasks.alert_all_owners') as alert_mock:
                with patch.object(site_check, 'retry', side_effect=Retry('retrying')) as retry_mock:
                    site_check.apply(args=[site.id, site.link]) 
        retry_mock.assert_called_once()
        assert SiteResponse.objects.count() == 0
        alert_mock.assert_not_called()

    def test_timeout_error_record(self, site):
        with patch('dashboard.tasks.requests.head', side_effect = requests.exceptions.Timeout()):
            with patch('dashboard.tasks.alert_all_owners'):
                site_check.apply(args = [site.id, site.link], retries = 3)
        assert SiteResponse.objects.get().error == 'TIMEOUT'