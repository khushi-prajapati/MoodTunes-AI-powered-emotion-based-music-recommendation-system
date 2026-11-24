from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('created_at', 'date_joined', 'last_login')
    list_per_page = 25
    date_hierarchy = 'created_at'
    fieldsets = UserAdmin.fieldsets + (
        ('MoodTunes metadata', {'fields': ('created_at',)}),
    )
