from django.db import models
from django.contrib.auth.models import AbstractUser


class Token(models.Model):
    token = models.CharField(max_length=64, unique=True)
    telegram_id = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]


class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True)
