from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
UserModel = get_user_model()


class Site(models.Model):
    owners = models.ManyToManyField(UserModel, related_name="sites")
    link = models.URLField(max_length=255, unique=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class SiteResponse(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="responses")
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_time = models.PositiveSmallIntegerField(null=True, blank=True)
    error = models.CharField(max_length=100, null=True, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["site", "-checked_at"]),
        ]
