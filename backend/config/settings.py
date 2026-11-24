import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_list(name: str, default: str = '') -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-development-only'
    else:
        raise RuntimeError('SECRET_KEY must be set when DEBUG is false.')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'authentication',
    'ai_emotion',
    'analytics',
    'music',
    'users',
]

AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.AdminNoStoreMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173',
)
FRONTEND_SITE_URL = os.getenv('FRONTEND_SITE_URL', 'http://localhost:5173')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('DRF_ANON_THROTTLE_RATE', '60/min'),
        'user': os.getenv('DRF_USER_THROTTLE_RATE', '600/min'),
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', '30'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', '7'))),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
SPOTIFY_MARKET = os.getenv('SPOTIFY_MARKET', 'US')

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', '300'))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '240'))
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', '1'))
CELERY_TASK_DEFAULT_QUEUE = os.getenv('CELERY_TASK_DEFAULT_QUEUE', 'default')
CELERY_TASK_ROUTES = {
    'tasks.analytics_tasks.*': {'queue': 'analytics'},
    'tasks.cleanup_tasks.*': {'queue': 'maintenance'},
    'tasks.recommendation_tasks.*': {'queue': 'recommendations'},
}
REDIS_CACHE_URL = os.getenv('REDIS_CACHE_URL', '')
CACHES = {
    'default': (
        {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_CACHE_URL,
        }
        if REDIS_CACHE_URL
        else {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'moodtunes-local-cache',
        }
    )
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = os.getenv('CSRF_COOKIE_HTTPONLY', 'False').lower() == 'true'
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

JAZZMIN_SETTINGS = {
    'site_title': 'MoodTunes Admin',
    'site_header': 'MoodTunes Administration',
    'site_brand': 'MoodTunes',
    'welcome_sign': 'Welcome to the MoodTunes administration console',
    'copyright': 'MoodTunes',
    'search_model': ['users.User', 'music.MoodHistory', 'music.RecommendedSong', 'music.Favorite', 'music.Playlist'],
    'site_logo': 'admin/branding/moodtunes-logo.svg',
    'login_logo': 'admin/branding/moodtunes-logo.svg',
    'login_logo_dark': 'admin/branding/moodtunes-logo.svg',
    'site_icon': 'admin/branding/favicon.svg',
    'custom_js': 'admin/js/moodtunes-admin.js',
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': ['authentication'],
    'order_with_respect_to': ['users', 'music'],
    'topmenu_links': [
        {
            'name': 'Main site',
            'url': '/admin/main-site/',
            'new_window': False,
            'icon': 'fas fa-external-link-alt',
        },
    ],
    'icons': {
        'auth.Group': 'fas fa-users-cog',
        'users.User': 'fas fa-user',
        'music.MoodHistory': 'fas fa-heart',
        'music.RecommendedSong': 'fas fa-music',
        'music.Favorite': 'fas fa-star',
        'music.Playlist': 'fas fa-list',
        'music.PlaylistSong': 'fas fa-record-vinyl',
        'ai_emotion.EmotionDetectionHistory': 'fas fa-smile',
        'analytics.AnalyticsSnapshot': 'fas fa-chart-bar',
    },
    'custom_links': {
        'music': [
            {
                'name': 'Mood history report',
                'url': 'admin:music_moodhistory_changelist',
                'icon': 'fas fa-chart-line',
                'permissions': ['music.view_moodhistory'],
            },
            {
                'name': 'Recommendation library',
                'url': 'admin:music_recommendedsong_changelist',
                'icon': 'fas fa-compact-disc',
                'permissions': ['music.view_recommendedsong'],
            },
        ],
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
    },
}

AI_EMOTION_USE_MTCNN = os.getenv('AI_EMOTION_USE_MTCNN', 'False').lower() == 'true'
AI_EMOTION_MAX_IMAGE_BYTES = int(os.getenv('AI_EMOTION_MAX_IMAGE_BYTES', '2500000'))
AI_EMOTION_MAX_IMAGE_DIMENSION = int(os.getenv('AI_EMOTION_MAX_IMAGE_DIMENSION', '960'))
AI_EMOTION_MPLCONFIG_DIR = os.getenv('AI_EMOTION_MPLCONFIG_DIR', '/tmp/moodtunes-matplotlib')
AI_EMOTION_FONT_CACHE_DIR = os.getenv('AI_EMOTION_FONT_CACHE_DIR', '/tmp/moodtunes-cache')

JAZZMIN_UI_TWEAKS = {
    'theme': 'flatly',
    'dark_mode_theme': 'darkly',
    'navbar': 'navbar-dark navbar-teal',
    'sidebar': 'sidebar-dark-primary',
    'accent': 'accent-teal',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-outline-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
    'actions_sticky_top': True,
}
