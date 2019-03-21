from biostar.settings.base import *

DEBUG = 0
TEMPLATE_DEBUG = 0

USE_COMPRESSOR = False

SITE_NAME = get_env("SITE_NAME", "Site Name")

DATABASES = {
    'default': {
        # To ENGINE 'django.db.backends.XYZ'
        # add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_NAME,
        'USER': 'biostar',
        'PASSWORD': get_env("PG_PASSWORD"),
        'HOST': get_env("PG_HOST"),
        'PORT': '5432',
    }
}
