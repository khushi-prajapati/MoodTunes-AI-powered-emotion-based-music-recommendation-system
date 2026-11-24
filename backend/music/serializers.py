from rest_framework import serializers

from .constants import SUPPORTED_MOODS
from .models import Favorite, MoodHistory, Playlist, PlaylistSong, RecommendedSong


class MoodSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()
    icon = serializers.CharField()


class RecommendRequestSerializer(serializers.Serializer):
    mood = serializers.ChoiceField(choices=list(SUPPORTED_MOODS.keys()))


class RecommendedSongSerializer(serializers.ModelSerializer):
    videoId = serializers.CharField(source='youtube_video_id')
    thumbnail = serializers.URLField(source='thumbnail_url')
    channel = serializers.CharField(source='channel_title')
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = RecommendedSong
        fields = (
            'id',
            'mood',
            'title',
            'videoId',
            'thumbnail',
            'channel',
            'youtube_video_id',
            'thumbnail_url',
            'channel_title',
            'created_at',
            'is_favorite',
        )
        read_only_fields = fields

    def get_is_favorite(self, obj):
        favorite_song_ids = self.context.get('favorite_song_ids')

        if favorite_song_ids is not None:
            return obj.id in favorite_song_ids

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return Favorite.objects.filter(user=request.user, song=obj).exists()


class MoodHistorySerializer(serializers.ModelSerializer):
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = MoodHistory
        fields = ('id', 'mood', 'searched_at', 'recommendations')
        read_only_fields = fields

    def get_recommendations(self, obj):
        next_search = MoodHistory.objects.filter(
            user=obj.user,
            searched_at__gt=obj.searched_at,
        ).order_by('searched_at').first()
        songs = RecommendedSong.objects.filter(
            user=obj.user,
            mood=obj.mood,
            created_at__gte=obj.searched_at,
        )

        if next_search:
            songs = songs.filter(created_at__lt=next_search.searched_at)

        songs = songs.order_by('created_at')[:10]
        return RecommendedSongSerializer(songs, many=True, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    song = RecommendedSongSerializer(read_only=True)
    song_id = serializers.PrimaryKeyRelatedField(
        queryset=RecommendedSong.objects.none(),
        source='song',
        write_only=True,
    )

    class Meta:
        model = Favorite
        fields = ('id', 'song', 'song_id', 'created_at')
        read_only_fields = ('id', 'song', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            self.fields['song_id'].queryset = RecommendedSong.objects.filter(user=request.user)

    def validate(self, attrs):
        request = self.context['request']
        song = attrs['song']

        if Favorite.objects.filter(user=request.user, song=song).exists():
            raise serializers.ValidationError({'song_id': 'This song is already in your favorites.'})

        return attrs

    def create(self, validated_data):
        return Favorite.objects.create(user=self.context['request'].user, **validated_data)


class PlaylistSongSerializer(serializers.ModelSerializer):
    song = RecommendedSongSerializer(read_only=True)

    class Meta:
        model = PlaylistSong
        fields = ('id', 'song', 'added_at')
        read_only_fields = fields


class PlaylistSerializer(serializers.ModelSerializer):
    song_count = serializers.SerializerMethodField()
    songs = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ('id', 'name', 'description', 'created_at', 'song_count', 'songs')
        read_only_fields = ('id', 'created_at', 'song_count', 'songs')

    def validate_name(self, value):
        request = self.context['request']
        playlist_id = self.instance.id if self.instance else None
        duplicate = Playlist.objects.filter(user=request.user, name__iexact=value)

        if playlist_id:
            duplicate = duplicate.exclude(id=playlist_id)

        if duplicate.exists():
            raise serializers.ValidationError('You already have a playlist with this name.')

        return value

    def create(self, validated_data):
        return Playlist.objects.create(user=self.context['request'].user, **validated_data)

    def get_songs(self, obj):
        playlist_songs = obj.playlist_songs.select_related('song')
        return PlaylistSongSerializer(playlist_songs, many=True, context=self.context).data

    def get_song_count(self, obj):
        return getattr(obj, 'song_count', obj.playlist_songs.count())


class PlaylistSongWriteSerializer(serializers.Serializer):
    song_id = serializers.PrimaryKeyRelatedField(queryset=RecommendedSong.objects.none(), source='song')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            self.fields['song_id'].queryset = RecommendedSong.objects.filter(user=request.user)

    def validate(self, attrs):
        playlist = self.context['playlist']
        song = attrs['song']

        if PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
            raise serializers.ValidationError({'song_id': 'This song is already in the playlist.'})

        return attrs
