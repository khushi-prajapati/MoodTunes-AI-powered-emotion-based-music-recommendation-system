from django.db.models import Count, Prefetch
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import SUPPORTED_MOODS
from .models import Favorite, MoodHistory, Playlist, PlaylistSong, RecommendedSong
from .serializers import (
    FavoriteSerializer,
    MoodHistorySerializer,
    MoodSerializer,
    PlaylistSerializer,
    PlaylistSongSerializer,
    PlaylistSongWriteSerializer,
    RecommendRequestSerializer,
    RecommendedSongSerializer,
)
from .services import YouTubeRecommendationService
from .spotify import SpotifyService


class MoodListView(APIView):
    def get(self, request):
        moods = [
            {'value': key, 'label': value['label'], 'icon': value['icon']}
            for key, value in SUPPORTED_MOODS.items()
        ]
        return Response(MoodSerializer(moods, many=True).data)


class RecommendView(APIView):
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mood = serializer.validated_data['mood']
        songs = YouTubeRecommendationService().search_by_mood(mood, max_results=10)
        MoodHistory.objects.create(user=request.user, mood=mood)

        saved_songs = [
            RecommendedSong.objects.create(user=request.user, mood=mood, **song)
            for song in songs
        ]

        return Response(
            {
                'mood': mood,
                'songs': RecommendedSongSerializer(
                    saved_songs,
                    many=True,
                    context={'request': request, 'favorite_song_ids': set()},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SpotifySearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'detail': 'Search query is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            limit = min(int(request.query_params.get('limit', 10)), 20)
        except ValueError:
            limit = 10
        return Response({'results': SpotifyService().search_tracks(query, limit=limit)})


class SpotifyPlaylistView(APIView):
    def get(self, request):
        playlist = request.query_params.get('playlist', '').strip()
        if not playlist:
            return Response({'detail': 'Spotify playlist URL or id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            limit = min(int(request.query_params.get('limit', 25)), 50)
        except ValueError:
            limit = 25

        return Response(SpotifyService().get_playlist(playlist, limit=limit))


class SpotifyArtistView(APIView):
    def get(self, request, artist_id):
        return Response(SpotifyService().get_artist(artist_id))


class RecommendationHistoryView(generics.ListAPIView):
    serializer_class = MoodHistorySerializer
    pagination_class = None

    def get_queryset(self):
        return MoodHistory.objects.filter(user=self.request.user).order_by('-searched_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['favorite_song_ids'] = set(
            Favorite.objects.filter(user=self.request.user).values_list('song_id', flat=True)
        )
        return context


class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    pagination_class = None

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('song').order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['favorite_song_ids'] = set(self.get_queryset().values_list('song_id', flat=True))
        return context


class FavoriteDeleteView(APIView):
    def delete(self, request, song_id):
        deleted_count, _ = Favorite.objects.filter(user=request.user, song_id=song_id).delete()

        if deleted_count == 0:
            return Response({'detail': 'Favorite not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistViewSet(viewsets.ModelViewSet):
    serializer_class = PlaylistSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        song_queryset = PlaylistSong.objects.select_related('song')
        return (
            Playlist.objects.filter(user=self.request.user)
            .annotate(song_count=Count('playlist_songs'))
            .prefetch_related(Prefetch('playlist_songs', queryset=song_queryset))
            .order_by('-created_at')
        )

    @action(detail=True, methods=['post'], url_path='songs')
    def add_song(self, request, pk=None):
        playlist = self.get_object()
        serializer = PlaylistSongWriteSerializer(
            data=request.data,
            context={'request': request, 'playlist': playlist},
        )
        serializer.is_valid(raise_exception=True)
        playlist_song = PlaylistSong.objects.create(playlist=playlist, song=serializer.validated_data['song'])

        return Response(
            PlaylistSongSerializer(playlist_song, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['delete'], url_path=r'songs/(?P<song_id>[0-9]+)')
    def remove_song(self, request, pk=None, song_id=None):
        playlist = self.get_object()
        deleted_count, _ = PlaylistSong.objects.filter(playlist=playlist, song_id=song_id).delete()

        if deleted_count == 0:
            return Response({'detail': 'Song not found in this playlist.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
