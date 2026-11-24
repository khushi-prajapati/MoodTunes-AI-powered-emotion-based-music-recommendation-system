from django.contrib import admin
from django.utils.html import format_html

from .models import Favorite, MoodHistory, Playlist, PlaylistSong, RecommendedSong


@admin.register(MoodHistory)
class MoodHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'searched_at')
    list_filter = ('mood', 'searched_at')
    search_fields = ('user__username', 'user__email', 'mood')
    ordering = ('-searched_at',)
    readonly_fields = ('searched_at',)
    autocomplete_fields = ('user',)
    list_per_page = 25
    date_hierarchy = 'searched_at'


@admin.register(RecommendedSong)
class RecommendedSongAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'mood', 'channel_title', 'youtube_link', 'created_at')
    list_filter = ('mood', 'created_at')
    search_fields = ('title', 'channel_title', 'user__username', 'youtube_video_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'thumbnail_preview', 'youtube_link')
    autocomplete_fields = ('user',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Recommendation', {'fields': ('user', 'mood', 'title', 'channel_title')}),
        ('YouTube media', {'fields': ('youtube_video_id', 'youtube_link', 'thumbnail_url', 'thumbnail_preview')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    @admin.display(description='YouTube')
    def youtube_link(self, obj):
        if not obj.youtube_video_id:
            return '-'

        url = f'https://www.youtube.com/watch?v={obj.youtube_video_id}'
        return format_html('<a href="{}" target="_blank" rel="noopener">Open video</a>', url)

    @admin.display(description='Thumbnail')
    def thumbnail_preview(self, obj):
        if not obj.thumbnail_url:
            return '-'

        return format_html(
            '<img src="{}" alt="{}" style="height: 72px; border-radius: 6px;" />',
            obj.thumbnail_url,
            obj.title,
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'created_at')
    list_filter = ('created_at', 'song__mood')
    search_fields = ('user__username', 'user__email', 'song__title', 'song__youtube_video_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'song')
    list_per_page = 25
    date_hierarchy = 'created_at'


class PlaylistSongInline(admin.TabularInline):
    model = PlaylistSong
    extra = 0
    autocomplete_fields = ('song',)
    readonly_fields = ('added_at',)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'song_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user',)
    inlines = (PlaylistSongInline,)
    list_per_page = 25
    date_hierarchy = 'created_at'

    @admin.display(description='Songs')
    def song_count(self, obj):
        return obj.playlist_songs.count()


@admin.register(PlaylistSong)
class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'song', 'added_at')
    list_filter = ('added_at', 'song__mood')
    search_fields = ('playlist__name', 'playlist__user__username', 'song__title', 'song__youtube_video_id')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)
    autocomplete_fields = ('playlist', 'song')
    list_per_page = 25
    date_hierarchy = 'added_at'
