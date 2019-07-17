from .base import *
from django.utils.log import DEFAULT_LOGGING

DEBUG = False
DEFAULT_LOGGING['handlers']['console']['filters'] = []  # Not Debug, yet Verbose

# For security check run: biostar.sh writer-prod check --deploy
# 2019-03-25 No SSL for writer
# SECURE_HSTS_SECONDS=3600  # https://docs.djangoproject.com/en/2.1/ref/middleware/#http-strict-transport-security
# SECURE_SSL_REDIRECT=True  # https://docs.djangoproject.com/en/2.1/ref/settings/#secure-ssl-redirect

ALLOWED_HOSTS = ['127.0.0.1']  # https://docs.djangoproject.com/en/2.1/ref/settings/#allowed-hosts

CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True

with open('/etc/biostar/writer-django-secret') as django_secret:
    SECRET_KEY = django_secret.read().strip()

with open('/etc/biostar/writer-dbpass') as dbpass:
    with open('/etc/biostar/dbhost') as dbhost:
        DATABASES = {
            'default': {
                # To ENGINE 'django.db.backends.XYZ'
                # add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'biostar',  # database name
                'USER': 'biostar',
                'PASSWORD': dbpass.read().strip(),
                'HOST': dbhost.read().strip(),
                'PORT': '5432',
            }
        }

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += ["rest_framework.authentication.TokenAuthentication"]

REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', [])
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] += ["rest_framework.permissions.IsAuthenticated"]
