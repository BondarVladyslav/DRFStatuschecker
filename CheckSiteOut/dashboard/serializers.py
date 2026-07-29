from datetime import timedelta

from django.db.models import Q
from django.db.models.aggregates import Avg, Count
from django.utils import timezone
from rest_framework.serializers import ModelSerializer, SerializerMethodField, ValidationError
from .models import Site, SiteResponse
from django.core.validators import URLValidator
class SiteSerializer(ModelSerializer):
    class Meta:
        model = Site
        fields = ['link', 'id']

    def validate_link(self, value):
        link = value if value.startswith(('http://', 'https://')) else 'https://' + value
        URLValidator()(link)              
        return link     

class SiteResponseSerializer(ModelSerializer):
    class Meta:
        model = SiteResponse
        fields = ['status_code', 'response_time', 'error', 'checked_at', 'id']
        

class SiteDetailSerializer(ModelSerializer):
    stats = SerializerMethodField()
    class Meta:
        model = Site
        fields = ['link','stats', 'id']


    def get_stats(self, obj):
        since = timezone.now() - timedelta(hours=24)
        return SiteResponse.objects.filter(
            site=obj, checked_at__gte=since
        ).aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(error__isnull=True)),
            avg_response_time=Avg('response_time'),
        )