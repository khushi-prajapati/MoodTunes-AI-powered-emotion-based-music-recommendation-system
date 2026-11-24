import json

from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count

from ai_emotion.models import EmotionDetectionHistory
from music.models import Favorite, MoodHistory, Playlist, RecommendedSong

register = template.Library()


@register.simple_tag
def frontend_site_url():
    return settings.FRONTEND_SITE_URL


@register.simple_tag
def admin_main_site_url():
    return '/admin/main-site/'


@register.simple_tag
def moodtunes_admin_metrics():
    User = get_user_model()
    top_mood = (
        MoodHistory.objects.values('mood')
        .annotate(total=Count('id'))
        .order_by('-total', 'mood')
        .first()
    )

    mood_rows = list(
        MoodHistory.objects.values('mood')
        .annotate(total=Count('id'))
        .order_by('-total', 'mood')[:6]
    )
    emotion_rows = list(
        EmotionDetectionHistory.objects.values('detected_emotion')
        .annotate(total=Count('id'))
        .order_by('-total', 'detected_emotion')[:6]
    )

    return {
        'total_users': User.objects.count(),
        'mood_searches': MoodHistory.objects.count(),
        'recommendations': RecommendedSong.objects.count(),
        'favorites': Favorite.objects.count(),
        'playlists': Playlist.objects.count(),
        'emotion_scans': EmotionDetectionHistory.objects.count(),
        'top_mood': top_mood['mood'] if top_mood else 'None',
        'mood_labels': json.dumps([row['mood'] for row in mood_rows]),
        'mood_values': json.dumps([row['total'] for row in mood_rows]),
        'emotion_labels': json.dumps([row['detected_emotion'] for row in emotion_rows]),
        'emotion_values': json.dumps([row['total'] for row in emotion_rows]),
    }
