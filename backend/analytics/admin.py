from django.contrib import admin

from .models import AnalyticsSnapshot


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('metrics', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 25
