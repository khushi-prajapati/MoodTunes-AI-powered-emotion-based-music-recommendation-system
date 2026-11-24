from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from ai_emotion.models import EmotionDetectionHistory
from music.models import Favorite, MoodHistory, Playlist, PlaylistSong, RecommendedSong


def build_analytics_payload(user=None):
    now = timezone.now()
    since = now - timedelta(days=30)
    User = get_user_model()
    mood_queryset = MoodHistory.objects.all()
    song_queryset = RecommendedSong.objects.all()
    favorite_queryset = Favorite.objects.all()
    playlist_queryset = Playlist.objects.all()
    playlist_song_queryset = PlaylistSong.objects.all()
    emotion_queryset = EmotionDetectionHistory.objects.all()

    if user:
        mood_queryset = mood_queryset.filter(user=user)
        song_queryset = song_queryset.filter(user=user)
        favorite_queryset = favorite_queryset.filter(user=user)
        playlist_queryset = playlist_queryset.filter(user=user)
        playlist_song_queryset = playlist_song_queryset.filter(playlist__user=user)
        emotion_queryset = emotion_queryset.filter(user=user)

    active_user_ids = set(mood_queryset.filter(searched_at__gte=since).values_list('user_id', flat=True))
    active_user_ids.update(emotion_queryset.filter(created_at__gte=since).values_list('user_id', flat=True))

    return {
        'summary': {
            'total_users': User.objects.count() if not user else 1,
            'active_users_30d': len(active_user_ids),
            'recommendations': song_queryset.count(),
            'favorites': favorite_queryset.count(),
            'playlists': playlist_queryset.count(),
            'playlist_songs': playlist_song_queryset.count(),
            'emotion_scans': emotion_queryset.count(),
        },
        'favorite_moods': _count_values(mood_queryset, 'mood', 'searched_at'),
        'emotion_trends': _count_values(emotion_queryset, 'detected_emotion', 'created_at'),
        'mapped_mood_trends': _count_values(emotion_queryset, 'mapped_mood', 'created_at'),
        'recommendation_frequency': _count_by_day(song_queryset, 'created_at'),
        'top_songs': list(
            song_queryset.values('title', 'channel_title')
            .annotate(total=Count('id'))
            .order_by('-total', 'title')[:10]
        ),
        'playlist_statistics': {
            'total_playlists': playlist_queryset.count(),
            'saved_playlist_songs': playlist_song_queryset.count(),
            'top_playlist_moods': _count_values(playlist_song_queryset, 'song__mood', 'added_at'),
        },
    }


def _count_values(queryset, field, date_field):
    rows = (
        queryset.values(field)
        .annotate(total=Count('id'))
        .order_by('-total', field)[:10]
    )
    return [{'label': row[field] or 'Unknown', 'total': row['total']} for row in rows]


def _count_by_day(queryset, date_field):
    rows = (
        queryset.annotate(day=TruncDate(date_field))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')[:30]
    )
    return [{'day': str(row['day']), 'total': row['total']} for row in rows]
