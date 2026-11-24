from music.constants import SUPPORTED_MOODS


EMOTION_TO_MOOD = {
    'angry': 'energetic',
    'disgust': 'angry',
    'fear': 'relaxed',
    'happy': 'happy',
    'neutral': 'relaxed',
    'sad': 'sad',
    'surprise': 'energetic',
}


def map_emotion_to_mood(emotion):
    mood = EMOTION_TO_MOOD.get(emotion, 'relaxed')

    if mood not in SUPPORTED_MOODS:
        return 'relaxed'

    return mood
