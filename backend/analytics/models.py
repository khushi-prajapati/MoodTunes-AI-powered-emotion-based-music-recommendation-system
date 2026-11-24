from django.db import models


class AnalyticsSnapshot(models.Model):
    metrics = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Analytics snapshot {self.created_at:%Y-%m-%d %H:%M}'
