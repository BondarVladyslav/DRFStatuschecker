from datetime import timedelta

from django.utils import timezone
import pytest
from django.test import TestCase
from dashboard.models import SiteResponse
from dashboard.serializers import SiteDetailSerializer, SiteSerializer


class TestSiteSerializerLinkValidating:

    @pytest.mark.parametrize(
            'link, result',
            [
                ('link.com', 'https://link.com'),
                ('ua.link.com','https://ua.link.com'),
            ],
    )
    def test_add_scheme(self,link, result):
        serializer = SiteSerializer(
            data = {
                'link':link
            }
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['link'] == result


    @pytest.mark.parametrize(
            'link, result',
            [
                ('https://link.com', 'https://link.com'),
                ('http://link.com','http://link.com'),
            ],
    )
    def test_does_not_change_existing_scheme(self,link,result):
        serializer = SiteSerializer(
            data = {
                'link':link
            }
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['link'] == result


    @pytest.mark.parametrize(
        'link',[0, 'l i n k', 'http://broken', 'https://']
    )
    def test_rejecting_invalid_url(self, link):
        serializer = SiteSerializer(
            data = {
                'link':link
            }
        )
        assert not serializer.is_valid()
        assert 'link' in serializer.errors


class TestSiteDetailSerializerStats:
    
    def test_24_hours_only_count(self, make_response, site):
        make_response(response_time = 100)
        make_response(response_time = 300, error = 'Bad status code 500')
        old = make_response(response_time = 500)
        SiteResponse.objects.filter(
            pk = old.pk
        ).update(
            checked_at = timezone.now()-timedelta(hours=25)
        )
        stats = SiteDetailSerializer(site).data['stats']
        assert stats['total'] == 2
        assert stats['successful'] == 1
        assert stats['avg_response_time'] == 200

    def test_stats_without_responses(self, site):
        stats = SiteDetailSerializer(site).data['stats']
        assert stats['total'] == 0
        assert stats['successful'] == 0
        assert stats['avg_response_time'] == None