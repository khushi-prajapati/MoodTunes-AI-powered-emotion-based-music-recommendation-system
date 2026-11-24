import requests
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException

from .constants import SUPPORTED_MOODS


class YouTubeServiceError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Unable to fetch recommendations from YouTube.'
    default_code = 'youtube_service_error'


class YouTubeConfigurationError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'YouTube API key is not configured.'
    default_code = 'youtube_api_key_missing'


class YouTubeRecommendationService:
    SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

    def __init__(self, api_key=None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY

    def search_by_mood(self, mood, max_results=10):
        if mood not in SUPPORTED_MOODS:
            raise ValueError('Unsupported mood.')

        if not self.api_key:
            raise YouTubeConfigurationError()

        params = {
            'part': 'snippet',
            'q': SUPPORTED_MOODS[mood]['query'],
            'type': 'video',
            'videoCategoryId': '10',
            'maxResults': max_results,
            'safeSearch': 'moderate',
            'key': self.api_key,
        }

        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise YouTubeServiceError(str(exc)) from exc

        return [
            self._parse_item(item)
            for item in response.json().get('items', [])
            if item.get('id', {}).get('videoId')
        ]

    def _parse_item(self, item):
        snippet = item.get('snippet', {})
        thumbnails = snippet.get('thumbnails', {})
        thumbnail = thumbnails.get('high') or thumbnails.get('medium') or thumbnails.get('default') or {}

        return {
            'title': snippet.get('title', 'Untitled'),
            'youtube_video_id': item['id']['videoId'],
            'thumbnail_url': thumbnail.get('url', ''),
            'channel_title': snippet.get('channelTitle', ''),
        }
