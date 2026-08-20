import pytest
from django.contrib.auth import get_user_model
from dashboard.models import Site, SiteResponse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tg_01", telegram_id=1)


@pytest.fixture
def second_user(db):
    return User.objects.create_user(username="tg_02", telegram_id=2)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def site(user):
    site = Site.objects.create(link="https://example.com/")
    site.owners.add(user)
    return site


@pytest.fixture
def make_response(site):
    def make_func(status_code=200, response_time=200, error=None, target=None):
        return SiteResponse.objects.create(
            site=target or site,
            status_code=status_code,
            response_time=response_time,
            error=error,
        )

    return make_func
