from datetime import timedelta
from urllib.parse import urlsplit
from .ipadressresolving import check_ip_blocked
from .exceptions import HostUnresolvable
from django.db.models import Q
from django.db.models.aggregates import Avg, Count
from django.utils import timezone
from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)
from .models import Site, SiteResponse
from django.core.validators import URLValidator


class SiteSerializer(ModelSerializer):
    link = CharField(max_length=255)

    class Meta:
        model = Site
        fields = ["link", "id"]

    def validate_link(self, value):
        link = (
            value
            if value.lower().startswith(("http://", "https://"))
            else "https://" + value
        )
        link = link.split("#")[0]
        base, sep, query = link.partition("?")
        scheme, proto_sep, rest = base.partition("://")
        host, slash, path = rest.partition("/")
        base = scheme.lower() + proto_sep + host.lower() + slash + path
        if base.count("/") < 3:
            base += "/"

        link = base + sep + query
        try:
            if check_ip_blocked(urlsplit(link).hostname):
                raise ValidationError("Host is not allowed")
        except HostUnresolvable:
            raise ValidationError("Host could not be resolved")
        URLValidator()(link)

        return link


class SiteResponseSerializer(ModelSerializer):
    class Meta:
        model = SiteResponse
        fields = ["status_code", "response_time", "error", "checked_at", "id"]


class SiteDetailSerializer(ModelSerializer):
    stats = SerializerMethodField()

    class Meta:
        model = Site
        fields = ["link", "stats", "id"]

    def get_stats(self, obj):
        since = timezone.now() - timedelta(hours=24)
        return SiteResponse.objects.filter(site=obj, checked_at__gte=since).aggregate(
            total=Count("id"),
            successful=Count("id", filter=Q(error__isnull=True)),
            avg_response_time=Avg("response_time"),
        )
