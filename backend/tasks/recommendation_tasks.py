import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from ai_emotion.services.recommendation_engine import PersonalizedRecommendationEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def generate_personalized_recommendations(self, user_id, mood, emotion=None, confidence=None):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    result = PersonalizedRecommendationEngine().recommend(
        user=user,
        mood=mood,
        emotion=emotion,
        confidence=confidence,
    )
    logger.info('Generated %s recommendations for user %s', len(result['songs']), user_id)
    return [song.id for song in result['songs']]
