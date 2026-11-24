from django.contrib import admin

from .models import EmotionDetectionHistory


@admin.register(EmotionDetectionHistory)
class EmotionDetectionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'detected_emotion', 'mapped_mood', 'confidence', 'created_at')
    list_filter = ('detected_emotion', 'mapped_mood', 'created_at')
    search_fields = ('user__username', 'user__email', 'detected_emotion', 'mapped_mood')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'detected_emotion', 'mapped_mood', 'confidence', 'created_at')
    autocomplete_fields = ('user',)
    list_per_page = 25
    date_hierarchy = 'created_at'
