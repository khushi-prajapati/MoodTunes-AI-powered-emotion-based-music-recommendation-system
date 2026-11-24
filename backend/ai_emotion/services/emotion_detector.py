import base64
import os
import tempfile
from binascii import Error as Base64Error
from functools import cached_property
from io import BytesIO

from django.conf import settings

from .mood_mapper import map_emotion_to_mood


class EmotionDetectionError(Exception):
    default_detail = 'Unable to detect emotion from this image.'

    def __init__(self, detail=None):
        super().__init__(detail or self.default_detail)
        self.detail = detail or self.default_detail


class InvalidImageError(EmotionDetectionError):
    default_detail = 'Invalid image data.'


class NoFaceDetectedError(EmotionDetectionError):
    default_detail = 'No face detected. Try centering your face and improving lighting.'


class EmotionEngineUnavailableError(EmotionDetectionError):
    default_detail = 'Emotion detection engine is not installed or could not be loaded.'


class EmotionDetector:
    @cached_property
    def detector(self):
        mpl_config_dir = getattr(settings, 'AI_EMOTION_MPLCONFIG_DIR', tempfile.gettempdir())
        os.makedirs(mpl_config_dir, exist_ok=True)
        os.environ.setdefault('MPLCONFIGDIR', mpl_config_dir)

        font_cache_dir = getattr(settings, 'AI_EMOTION_FONT_CACHE_DIR', tempfile.gettempdir())
        os.makedirs(font_cache_dir, exist_ok=True)
        os.environ.setdefault('XDG_CACHE_HOME', font_cache_dir)

        try:
            from fer.fer import FER
        except ImportError as exc:
            raise EmotionEngineUnavailableError(
                'Install AI dependencies with pip before using emotion detection.'
            ) from exc

        return FER(mtcnn=settings.AI_EMOTION_USE_MTCNN)

    def detect(self, image_data):
        image = self._decode_image(image_data)
        results = self.detector.detect_emotions(image)

        if not results:
            raise NoFaceDetectedError()

        face = self._select_primary_face(results)
        emotion, confidence = self._top_emotion(face.get('emotions', {}))

        if not emotion:
            raise EmotionDetectionError()

        return {
            'emotion': emotion,
            'confidence': round(float(confidence), 4),
            'mapped_mood': map_emotion_to_mood(emotion),
        }

    def _decode_image(self, image_data):
        try:
            import numpy as np
            from PIL import Image, ImageOps, UnidentifiedImageError
        except ImportError as exc:
            raise EmotionEngineUnavailableError(
                'Install AI dependencies with pip before using emotion detection.'
            ) from exc

        if not image_data:
            raise InvalidImageError()

        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]

        try:
            raw = base64.b64decode(image_data, validate=True)
        except (Base64Error, ValueError) as exc:
            raise InvalidImageError() from exc

        if len(raw) > settings.AI_EMOTION_MAX_IMAGE_BYTES:
            raise InvalidImageError('Image is too large.')

        try:
            image = Image.open(BytesIO(raw))
            image = ImageOps.exif_transpose(image).convert('RGB')
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidImageError() from exc

        image.thumbnail(
            (settings.AI_EMOTION_MAX_IMAGE_DIMENSION, settings.AI_EMOTION_MAX_IMAGE_DIMENSION)
        )
        return np.asarray(image)

    def _select_primary_face(self, results):
        return max(results, key=lambda item: item.get('box', [0, 0, 0, 0])[2] * item.get('box', [0, 0, 0, 0])[3])

    def _top_emotion(self, emotions):
        if not emotions:
            return None, 0

        return max(emotions.items(), key=lambda item: item[1])
