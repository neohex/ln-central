# -*- coding: utf8 -*-
#
# Development settings
#
from .base import *

# add debugging middleware
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# We load the debug toolbar as well
INSTALLED_APPS = list(INSTALLED_APPS)

# This needs to be added before the user models.
INSTALLED_APPS.append( "debug_toolbar")

def show_toolbar(request):
    return True

DEBUG_TOOLBAR_CONFIG ={}


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

