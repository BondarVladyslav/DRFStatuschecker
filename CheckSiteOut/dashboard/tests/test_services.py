import pytest
import json
from unittest.mock import patch
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from dashboard.services import add_site_for_user, stop_monitoring
from dashboard.models import Site
class TestAddingSiteForUser:

    def test_creating_and_adding_user_for_sit(self,user,django_capture_on_commit_callbacks):

        with patch('dashboard.services.site_check') as task:
            with django_capture_on_commit_callbacks(execute=True):
                site = add_site_for_user(link='https://link.com', user=user)

            assert Site.objects.count() == 1
            assert list(site.owners.all()) == [user]
            task.delay.assert_called_once_with(site.id, 'https://link.com')

        def test_creating_tasks_with_correct_params(self,user):
            with patch('dashboard.services.site_check'):
                site = add_site_for_user(link='https://link.com', user=user)
            task = PeriodicTask.objects.get(name=f'check_site{site.id}')
            assert task.task  == 'dashboard.services.site_check'
            assert json.loads(task.args) == [site.id,'https://link.com']
            assert task.interval.every == 1
            assert task.interval.period == IntervalSchedule.MINUTES

        def test_non_duplicating_tasks(self,user,second_user,django_capture_on_commit_callbacks):
            with patch('dashboard.services.site_check') as task:
                with django_capture_on_commit_callbacks(execute=True):
                    first_site = add_site_for_user(link='https://link.com', user=user)

                task.reset_mock()

                with django_capture_on_commit_callbacks(execute = True):
                    second_site = add_site_for_user(link='https://link.com', user = user)
                assert first_site.id == second_site.id
                assert Site.objects.count() == 1
                assert second_site.objects.count() == 2
                assert PeriodicTask.objects.count() == 1
                task.assert_not_called()

        def test_twice_try_of_same_user_does_not_nothing(self, user):
            with patch('dashboard.services.site_check'):
                add_site_for_user(link='https://link.com', user = user)
                site = add_site_for_user(link='https://link.com', user = user)
            assert site.owners.count() == 1


class TestStoppingMonitoring:
    def test_deletes_periodic_task(self, user):
        with patch('dashboard.services.site_check'):
            site = add_site_for_user(link='https://link.com', user = user)
        stop_monitoring(site.id)
        assert not PeriodicTask.objects.filter(name=f'check_site_{site.id}').exists()

    def test_unexisting_does_not_raise_problems(self, db):
        stop_monitoring('not_existing')