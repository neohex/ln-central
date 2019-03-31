"""
Django settings for biostar_writer project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# directory where manage.py lives
BASE_DIR = (
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )
)

SECURE_CONTENT_TYPE_NOSNIFF = True  # https://docs.djangoproject.com/en/2.1/ref/middleware/#x-content-type-options
SECURE_BROWSER_XSS_FILTER = True  # https://docs.djangoproject.com/en/2.1/ref/middleware/#x-xss-protection-1-mode-block
X_FRAME_OPTIONS = 'DENY'  # https://docs.djangoproject.com/en/2.1/ref/clickjacking/

# Application definition

INSTALLED_APPS = [
    # built-in
    'django.contrib.contenttypes',
    'django.contrib.auth',  # required by REST framework
    'django.contrib.sessions',  # required for auth
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # third-party
    'rest_framework',
    'rest_framework.authtoken',
    'background_task',

    # project
    'users',
    'lner'
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',  # required for auth
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # required for auth
    'django.middleware.csrf.CsrfViewMiddleware',  # useful, enabled by sessions
]

ROOT_URLCONF = 'biostar_writer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',  # required for auth
            ],
        },
    },
]

WSGI_APPLICATION = 'biostar_writer.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = []  # no password on this site


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'


# biostar-ln specific config
MOCK_LN_CLIENT = False
