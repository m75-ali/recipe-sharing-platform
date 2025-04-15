import os
from pathlib import Path
import dj_database_url

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-default-insecure-key')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['recipe-sharing-platform-1w5u.onrender.com', 'localhost', '127.0.0.1']

# Also ensure you have this for CSRF protection
CSRF_TRUSTED_ORIGINS = [
    'https://recipe-sharing-platform-1w5u.onrender.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'recipes',
    'recipesharing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be just after security middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'recipesharing.middleware.DebugMiddleware',  # Custom middleware for debugging
]

ROOT_URLCONF = 'recipesharing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'recipesharing.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_REDIRECT_URL = 'recipe_index'
LOGOUT_REDIRECT_URL = 'recipe_index'
LOGIN_URL = 'login'


# Cookie settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'  # Try 'Lax' if this doesn't work
CSRF_COOKIE_SAMESITE = 'None'     # Try 'Lax' if this doesn't work