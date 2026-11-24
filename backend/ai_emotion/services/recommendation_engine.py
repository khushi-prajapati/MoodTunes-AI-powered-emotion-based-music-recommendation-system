from collections import Counter

from django.db.models import Count

from music.models import Favorite, MoodHistory, PlaylistSong, RecommendedSong
from music.services import YouTubeRecommendationService

from ..models import EmotionDetectionHistory


class PersonalizedRecommendationEngine:
    def __init__(self, youtube_service=None):
        self.youtube_service = youtube_service or YouTubeRecommendationService()

    def recommend(self, user, mood, emotion=None, confidence=None, max_results=10):
        raw_songs = self.youtube_service.search_by_mood(mood, max_results=max_results)
        profile = self._build_profile(user)
        scored_songs = sorted(
            (self._score_song(song, mood, emotion, confidence, profile) for song in raw_songs),
            key=lambda item: item['score'],
            reverse=True,
        )

        MoodHistory.objects.create(user=user, mood=mood)
        saved_songs = [
            RecommendedSong.objects.create(user=user, mood=mood, **item['song'])
            for item in scored_songs
        ]

        return {
            'mood': mood,
            'emotion': emotion,
            'confidence': confidence,
            'songs': saved_songs,
            'personalization': self._summarize_profile(profile),
        }

    def _build_profile(self, user):
        favorite_songs = (
            Favorite.objects.filter(user=user)
            .select_related('song')
            .order_by('-created_at')[:50]
        )
        playlist_songs = (
            PlaylistSong.objects.filter(playlist__user=user)
            .select_related('song')
            .order_by('-added_at')[:100]
        )
        recent_moods = list(
            MoodHistory.objects.filter(user=user)
            .values_list('mood', flat=True)
            .order_by('-searched_at')[:20]
        )
        recent_emotions = list(
            EmotionDetectionHistory.objects.filter(user=user)
            .values_list('mapped_mood', flat=True)
            .order_by('-created_at')[:20]
        )

        channel_weights = Counter()
        title_terms = Counter()
        mood_weights = Counter(recent_moods)
        mood_weights.update(recent_emotions)

        for favorite in favorite_songs:
            self._add_song_signal(favorite.song, channel_weights, title_terms, weight=3)

        for playlist_song in playlist_songs:
            self._add_song_signal(playlist_song.song, channel_weights, title_terms, weight=2)

        repeated_channels = dict(
            RecommendedSong.objects.filter(user=user)
            .values('channel_title')
            .annotate(total=Count('id'))
            .order_by('-total')[:15]
            .values_list('channel_title', 'total')
        )

        return {
            'channel_weights': channel_weights,
            'title_terms': title_terms,
            'mood_weights': mood_weights,
            'repeated_channels': repeated_channels,
            'favorite_count': len(favorite_songs),
            'playlist_song_count': len(playlist_songs),
        }

    def _add_song_signal(self, song, channel_weights, title_terms, weight):
        if song.channel_title:
            channel_weights[song.channel_title.lower()] += weight

        for term in self._title_terms(song.title):
            title_terms[term] += weight

    def _score_song(self, song, mood, emotion, confidence, profile):
        channel = song.get('channel_title', '').lower()
        title_terms = self._title_terms(song.get('title', ''))
        score = 1.0
        signals = ['current mood']

        mood_boost = min(profile['mood_weights'].get(mood, 0) * 0.08, 0.4)
        if mood_boost:
            score += mood_boost
            signals.append('recent mood pattern')

        if emotion and confidence:
            confidence_boost = min(float(confidence) * 0.2, 0.2)
            score += confidence_boost
            signals.append('emotion confidence')

        if channel and channel in profile['channel_weights']:
            score += min(profile['channel_weights'][channel] * 0.12, 0.6)
            signals.append('saved channel affinity')

        if channel and channel in profile['repeated_channels']:
            score += min(profile['repeated_channels'][channel] * 0.04, 0.3)
            signals.append('listening frequency')

        title_match_score = sum(profile['title_terms'].get(term, 0) for term in title_terms)
        if title_match_score:
            score += min(title_match_score * 0.03, 0.35)
            signals.append('title similarity')

        return {
            'song': song,
            'score': round(score, 4),
            'signals': signals,
        }

    def _title_terms(self, title):
        stop_words = {'the', 'and', 'with', 'for', 'official', 'video', 'audio', 'lyrics'}
        normalized = ''.join(character.lower() if character.isalnum() else ' ' for character in title)
        return [
            term
            for term in normalized.split()
            if len(term) > 2 and term not in stop_words
        ]

    def _summarize_profile(self, profile):
        top_channels = [
            channel
            for channel, _ in profile['channel_weights'].most_common(3)
        ]
        top_moods = [
            mood
            for mood, _ in profile['mood_weights'].most_common(3)
        ]

        return {
            'favorite_count': profile['favorite_count'],
            'playlist_song_count': profile['playlist_song_count'],
            'top_channels': top_channels,
            'recent_moods': top_moods,
        }
