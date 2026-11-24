import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('moodtunes')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.include = [
    'tasks.analytics_tasks',
    'tasks.cleanup_tasks',
    'tasks.recommendation_tasks',
]
app.conf.beat_schedule = {
    'analytics-snapshot-hourly': {
        'task': 'tasks.analytics_tasks.generate_analytics_snapshot',
        'schedule': crontab(minute=0),
    },
    'cleanup-old-analytics-nightly': {
        'task': 'tasks.cleanup_tasks.cleanup_old_analytics_snapshots',
        'schedule': crontab(hour=3, minute=15),
    },
    'cleanup-expired-sessions-nightly': {
        'task': 'tasks.cleanup_tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=3, minute=30),
    },
}
