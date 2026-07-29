from django.db import models

# Create your models here.

class Token(models.Model):
    token = models.CharField(max_length=64)
    telegram_id = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']