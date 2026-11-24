from django.test import TestCase

from .spotify import SpotifyService


class SpotifyServiceTests(TestCase):
    def test_playlist_id_accepts_spotify_url(self):
        service = SpotifyService(client_id='client', client_secret='secret')

        self.assertEqual(
            service._playlist_id('https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=test'),
            '37i9dQZF1DXcBWIGoYBM5M',
        )

    def test_parse_track_returns_artist_metadata(self):
        service = SpotifyService(client_id='client', client_secret='secret')

        track = service._parse_track(
            {
                'id': 'track-id',
                'name': 'Song',
                'artists': [{'id': 'artist-id', 'name': 'Artist', 'external_urls': {'spotify': 'url'}}],
                'album': {'name': 'Album', 'images': [{'url': 'image'}]},
                'external_urls': {'spotify': 'track-url'},
            }
        )

        self.assertEqual(track['artists'][0]['id'], 'artist-id')
        self.assertEqual(track['image_url'], 'image')
