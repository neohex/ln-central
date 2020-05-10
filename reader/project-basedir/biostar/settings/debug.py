# -*- coding: utf8 -*-
#
# Development settings
#
from .base import *

# add debugging middleware
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)

TOOLBAR = False
if TOOLBAR:
    MIDDLEWARE_CLASSES.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

    # This needs to be added before the user models.
    INSTALLED_APPS.append( "debug_toolbar")
    DEBUG_TOOLBAR_CONFIG ={}

# We load the debug toolbar as well
INSTALLED_APPS = list(INSTALLED_APPS)

# Reader users the writers database
DATABASE_NAME = abspath(HOME_DIR, '..', '..', 'writer', 'project-basedir', 'live', 'db.sqlite3')
DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_NAME,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {}
    }
}

