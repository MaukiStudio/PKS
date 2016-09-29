"""
Django settings for pks project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
from settings_deploy import *


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

'''
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k-#u@ot7=juqps99cjy5wz78e0ljq0og#pv2a5&u2f@+4#n+i6'
USER_ENC_KEY = 'wEy-jbl4InBNmJh6hriCBsKomeQsS5wKe66dJPAHr-o='
VD_ENC_KEY = 'TTlrdjLDsgcN63Pjd9dU8CvZ4bllcL8nkJejTAR2EAY='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
'''
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'grappelli',
    'filebrowser',
    'django.contrib.admin',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'rest_framework',
    'django_extensions',

    'account',
    'image',
    'url',
    'content',
    'place',
    'importer',
    'tag',

    'admin2',
    'ui',
    'etc',
]

AUTH_USER_MODEL = 'account.User'

class DisableCSRF(object):
    def process_request(self, request):
        path_info = request.path_info
        if path_info.startswith('/ui') or path_info.startswith('/admin'):
            return
        setattr(request, '_dont_enforce_csrf_checks', True)

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'pks.settings.DisableCSRF',
]

ROOT_URLCONF = 'pks.urls'

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
                'django.core.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'pks.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
'''
DATABASES = {
    'default': {
        #'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'pks',
        'USER': 'pks_user',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
        'PORT': '',
    }
}


# DRF
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_METADATA_CLASS': 'pks.config.MinimalMetadata',
}


# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_AGE = 365 * 24 * 60 * 60


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, '../collected_static/')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, '../media/')


# pks
VD_SESSION_KEY = 'vd_session_key'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://%s:6379/1' % REDIS_SERVER_IP,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    }
}
