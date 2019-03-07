#!/bin/bash
set -ue

# Required environmental variables:
# * PROJECT_DIR
# * SITE_NAME
# * SITE_DOMAIN
# * PG_HOST
# * PG_PASSWORD

# This is required so that the default configuration file works.
source $PROJECT_DIR/live/deploy.env

# Setting the various access logs.
ACCESS_LOG=$PROJECT_DIR/live/logs/gunicorn-access.log
ERROR_LOG=$PROJECT_DIR/live/logs/gunicorn-error.log

# The user and group the unicorn process will run as.
NUM_WORKERS=3

# Where to bind.
BIND="unix:/tmp/biostar.sock"
#BIND="localhost:8080"

# The WSGI module that starts the process.
DJANGO_WSGI_MODULE='biostar.wsgi'

# The gunicorn instance to run.
GUNICORN="gunicorn"

# How many requests to serve.
MAX_REQUESTS=1000

# The name of the application.
NAME="biostar_app"

echo "gunicorn starting with DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

exec $GUNICORN ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --max-requests $MAX_REQUESTS\
  --bind $BIND\
