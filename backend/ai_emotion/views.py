from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from music.models import Favorite
from music.serializers import RecommendedSongSerializer

from .models import EmotionDetectionHistory
from .serializers import (
    EmotionDetectionRequestSerializer,
    EmotionDetectionResponseSerializer,
    PersonalizedRecommendationRequestSerializer,
)
from .services.emotion_detector import EmotionDetectionError, EmotionDetector
from .services.recommendation_engine import PersonalizedRecommendationEngine


class DetectEmotionView(APIView):
    def post(self, request):
        serializer = EmotionDetectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = EmotionDetector().detect(serializer.validated_data['image'])
        except EmotionDetectionError as exc:
            return Response({'detail': exc.detail}, status=status.HTTP_400_BAD_REQUEST)

        history = EmotionDetectionHistory.objects.create(
            user=request.user,
            detected_emotion=result['emotion'],
            mapped_mood=result['mapped_mood'],
            confidence=result['confidence'],
        )

        return Response(EmotionDetectionResponseSerializer(history).data, status=status.HTTP_200_OK)


class PersonalizedRecommendationView(APIView):
    def post(self, request):
        serializer = PersonalizedRecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = PersonalizedRecommendationEngine().recommend(
            user=request.user,
            mood=serializer.validated_data['mood'],
            emotion=serializer.validated_data.get('emotion'),
            confidence=serializer.validated_data.get('confidence'),
        )
        favorite_song_ids = set(
            Favorite.objects.filter(user=request.user).values_list('song_id', flat=True)
        )

        return Response(
            {
                'mood': result['mood'],
                'emotion': result['emotion'],
                'confidence': result['confidence'],
                'personalization': result['personalization'],
                'songs': RecommendedSongSerializer(
                    result['songs'],
                    many=True,
                    context={'request': request, 'favorite_song_ids': favorite_song_ids},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )
