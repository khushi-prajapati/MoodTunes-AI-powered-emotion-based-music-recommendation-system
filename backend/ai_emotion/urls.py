from django.urls import path

from .views import DetectEmotionView, PersonalizedRecommendationView

urlpatterns = [
    path('detect-emotion/', DetectEmotionView.as_view(), name='detect-emotion'),
    path('personalized-recommendations/', PersonalizedRecommendationView.as_view(), name='personalized-recommendations'),
]
