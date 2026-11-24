from rest_framework import serializers

from music.constants import SUPPORTED_MOODS
from .models import EmotionDetectionHistory


class EmotionDetectionRequestSerializer(serializers.Serializer):
    image = serializers.CharField(
        trim_whitespace=False,
        write_only=True,
        help_text='Base64 encoded image data or a browser data URL.',
    )


class EmotionDetectionResponseSerializer(serializers.ModelSerializer):
    emotion = serializers.CharField(source='detected_emotion')
    confidence = serializers.FloatField()

    class Meta:
        model = EmotionDetectionHistory
        fields = ('emotion', 'confidence', 'mapped_mood', 'created_at')
        read_only_fields = fields


class PersonalizedRecommendationRequestSerializer(serializers.Serializer):
    mood = serializers.ChoiceField(choices=list(SUPPORTED_MOODS.keys()))
    emotion = serializers.CharField(required=False, allow_blank=True, max_length=32)
    confidence = serializers.FloatField(required=False, min_value=0, max_value=1)
