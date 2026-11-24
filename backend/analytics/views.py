from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_analytics_payload


class AnalyticsDashboardView(APIView):
    def get(self, request):
        user = None if request.user.is_staff or request.user.is_superuser else request.user
        return Response(build_analytics_payload(user=user))
