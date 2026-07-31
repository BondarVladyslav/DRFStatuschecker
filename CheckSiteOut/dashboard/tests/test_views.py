from django.urls import reverse
import pytest
from unittest.mock import patch
from rest_framework import status

from dashboard.models import Site






def test_anon_user_does_401(api_client):
    response = api_client.get(reverse('dashboard-list'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateSite:
    def test_valid_link_creting(self, auth_client, user):
        with patch('dashboard.services.site_check'):
            response = auth_client.post(reverse('dashboard-list'), data = {'link':'link.com'})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['link'] == 'https://link.com'
        site = Site.objects.get()
        assert user in site.owners.all()

    def test_invalid_link_creating(self, auth_client, user):
        response = auth_client.post(reverse('dashboard-list'), data={'link':'invalid'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Site.objects.count() == 0

class TestList:
    def test_user_see_only_his_sites(self, auth_client,site, second_user):
        fk = Site.objects.create(link = 'https://link1.com')
        fk.owners.add(second_user)
        
        response = auth_client.get(reverse('dashboard-list'))
        assert response.status_code == status.HTTP_200_OK
        links = [k['link'] for k in response.data['results']]
        assert links == [site.link]
    def test_cant_retrieve_another_site(self, auth_client, second_user):
        fk = Site.objects.create(link = 'https://link.com')
        fk.owners.add(second_user)
        response = auth_client.get(reverse('dashboard-detail', args = [fk.id]))

        assert response.status_code == status.HTTP_404_NOT_FOUND

class TestRetrieve:
    def test_detail_response_stats(self,auth_client,site, make_response):
        make_response(response_time = 100)
        make_response(response_time = 200, error = 'Bad status code 500')

        response = auth_client.get(reverse('dashboard-detail', args=[site.id]))

        assert response.status_code == status.HTTP_200_OK

        assert response.data['stats'] == {
            'total':2,
            'successful':1,
            'avg_response_time':150
        }
class TestLeave:
    def last_leave_stops_monitoring(self, auth_client, site):
        with patch('dashboard.views.stop_monitoring') as stop_mock:
            response = auth_client.post(reverse('dashboard-leave', args=[site.id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Site.objects.filter(id=site.id).exists()

        stop_mock.assert_called_once_with(site.id)

    def test_leaving_with_remaining_owner_keeps_site(self, auth_client, site, second_user):

        site.owners.add(second_user)


        with patch('dashboard.views.stop_monitoring') as stop_mock:
            resp = auth_client.post(reverse('dashboard-leave', args=[site.id]))

        assert resp.status_code == status.HTTP_204_NO_CONTENT
        site.refresh_from_db()
        assert list(site.owners.all()) == [second_user]
        stop_mock.assert_not_called()

def test_pagination_of_responses(auth_client, site, make_response):     
    for i in range(30):      
        make_response(response_time=i)
    response = auth_client.get(reverse('dashboard-responses', args=[site.id]))
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 30
    assert len(response.data['results']) == 24
    assert response.data['next'] is not None
