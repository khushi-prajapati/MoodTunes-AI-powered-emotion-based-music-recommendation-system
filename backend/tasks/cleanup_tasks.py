import logging
from datetime import timedelta

from celery import shared_task
from django.core.management import call_command
from django.utils import timezone

from analytics.models import AnalyticsSnapshot

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def cleanup_old_analytics_snapshots(self, days=90):
    cutoff = timezone.now() - timedelta(days=days)
    deleted_count, _ = AnalyticsSnapshot.objects.filter(created_at__lt=cutoff).delete()
    logger.info('Deleted %s old analytics snapshots', deleted_count)
    return deleted_count


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def cleanup_expired_sessions(self):
    call_command('clearsessions')
    logger.info('Cleared expired Django sessions')
    return 'ok'
