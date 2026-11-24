import logging
from celery import shared_task

from analytics.models import AnalyticsSnapshot
from analytics.services import build_analytics_payload

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def generate_analytics_snapshot(self):
    payload = build_analytics_payload()
    snapshot = AnalyticsSnapshot.objects.create(metrics=payload)
    logger.info('Generated analytics snapshot %s', snapshot.id)
    return snapshot.id
