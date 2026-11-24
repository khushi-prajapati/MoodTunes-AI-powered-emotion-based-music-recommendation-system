import base64
import re
import time
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import InvalidCacheBackendError
from rest_framework import status
from rest_framework.exceptions import APIException


class SpotifyConfigurationError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Spotify API credentials are not configured.'
    default_code = 'spotify_credentials_missing'


class SpotifyServiceError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Unable to fetch data from Spotify.'
    default_code = 'spotify_service_error'


class SpotifyService:
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    API_URL = 'https://api.spotify.com/v1'

    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or settings.SPOTIFY_CLIENT_ID
        self.client_secret = client_secret or settings.SPOTIFY_CLIENT_SECRET

    def search_tracks(self, query, limit=10):
        params = {
            'q': query,
            'type': 'track',
            'limit': limit,
        }
        payload = self._get('/search', params=params)
        return [self._parse_track(item) for item in payload.get('tracks', {}).get('items', [])]

    def get_artist(self, artist_id):
        artist = self._get(f'/artists/{artist_id}')
        albums = self._get(
            f'/artists/{artist_id}/albums',
            params={'include_groups': 'album,single', 'limit': 8},
        )
        top_tracks = self._get(f'/artists/{artist_id}/top-tracks', params={'market': settings.SPOTIFY_MARKET})

        return {
            'id': artist.get('id'),
            'name': artist.get('name'),
            'genres': artist.get('genres', []),
            'popularity': artist.get('popularity', 0),
            'followers': artist.get('followers', {}).get('total', 0),
            'spotify_url': artist.get('external_urls', {}).get('spotify'),
            'image_url': self._image_url(artist.get('images', [])),
            'albums': [self._parse_album(item) for item in albums.get('items', [])],
            'top_tracks': [self._parse_track(item) for item in top_tracks.get('tracks', [])[:8]],
        }

    def get_playlist(self, playlist_url_or_id, limit=25):
        playlist_id = self._playlist_id(playlist_url_or_id)
        if not playlist_id:
            raise SpotifyServiceError('Invalid Spotify playlist URL or id.')

        payload = self._get(
            f'/playlists/{playlist_id}',
            params={'fields': 'id,name,description,external_urls,images,owner.display_name,tracks.items(track),tracks.total'},
        )
        tracks = [
            self._parse_track(item.get('track', {}))
            for item in payload.get('tracks', {}).get('items', [])[:limit]
            if item.get('track')
        ]

        return {
            'id': payload.get('id'),
            'name': payload.get('name'),
            'description': payload.get('description', ''),
            'owner': payload.get('owner', {}).get('display_name', ''),
            'spotify_url': payload.get('external_urls', {}).get('spotify'),
            'image_url': self._image_url(payload.get('images', [])),
            'track_total': payload.get('tracks', {}).get('total', len(tracks)),
            'tracks': tracks,
        }

    def _get(self, path, params=None):
        try:
            response = requests.get(
                f'{self.API_URL}{path}',
                params=params,
                headers={'Authorization': f'Bearer {self._access_token()}'},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SpotifyServiceError(str(exc)) from exc

        return response.json()

    def _access_token(self):
        if not self.client_id or not self.client_secret:
            raise SpotifyConfigurationError()

        cache_key = 'spotify_client_credentials_token'
        cached_token = self._cache_get(cache_key)
        if cached_token:
            return cached_token

        token = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={'grant_type': 'client_credentials'},
                headers={'Authorization': f'Basic {token}'},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SpotifyServiceError(str(exc)) from exc

        payload = response.json()
        expires_in = max(int(payload.get('expires_in', 3600)) - 60, 60)
        access_token = payload['access_token']
        self._cache_set(cache_key, access_token, timeout=expires_in)
        return access_token

    def _parse_track(self, item):
        album_images = item.get('album', {}).get('images', [])
        return {
            'id': item.get('id'),
            'title': item.get('name'),
            'artists': [
                {
                    'id': artist.get('id'),
                    'name': artist.get('name'),
                    'spotify_url': artist.get('external_urls', {}).get('spotify'),
                }
                for artist in item.get('artists', [])
            ],
            'album': item.get('album', {}).get('name', ''),
            'preview_url': item.get('preview_url'),
            'spotify_url': item.get('external_urls', {}).get('spotify'),
            'image_url': self._image_url(album_images),
            'popularity': item.get('popularity', 0),
            'duration_ms': item.get('duration_ms', 0),
            'fetched_at': int(time.time()),
        }

    def _parse_album(self, item):
        return {
            'id': item.get('id'),
            'name': item.get('name'),
            'release_date': item.get('release_date', ''),
            'total_tracks': item.get('total_tracks', 0),
            'spotify_url': item.get('external_urls', {}).get('spotify'),
            'image_url': self._image_url(item.get('images', [])),
        }

    def _image_url(self, images):
        return images[0]['url'] if images else ''

    def _playlist_id(self, value):
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            match = re.search(r'/playlist/([A-Za-z0-9]+)', parsed.path)
            return match.group(1) if match else ''

        return value.strip() if re.fullmatch(r'[A-Za-z0-9]+', value.strip()) else ''

    def _cache_get(self, key):
        try:
            return cache.get(key)
        except Exception:
            return None

    def _cache_set(self, key, value, timeout):
        try:
            cache.set(key, value, timeout=timeout)
        except (Exception, InvalidCacheBackendError):
            return
