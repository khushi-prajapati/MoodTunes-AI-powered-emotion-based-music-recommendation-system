from django.contrib import admin
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import include, path
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

admin.site.site_title = 'MoodTunes Admin'
admin.site.site_header = 'MoodTunes Administration'
admin.site.index_title = 'Welcome to MoodTunes Admin'
admin.site.index_template = 'admin/moodtunes_index.html'
admin.site.logout_template = 'admin/logged_out_redirect.html'
admin.site.site_url = '/admin/main-site/'


@never_cache
def admin_logout_to_frontend(request):
    logout(request)
    response = redirect(settings.FRONTEND_SITE_URL)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok', 'service': 'MoodTunes API'})


urlpatterns = [
    path('admin/main-site/', admin_logout_to_frontend, name='admin_main_site'),
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/ai/', include('ai_emotion.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/auth/', include('authentication.urls')),
    path('api/music/', include('music.urls')),
]
