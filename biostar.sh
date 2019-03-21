#!/bin/bash

if [ $# == 0 ]; then
    echo ''
    echo 'Usage:'
    echo ''
    echo "  $ $(basename $0) <command>"
    echo ''
    echo 'Multiple commands may be used on the same line:'
    echo ''
    echo "  $ $(basename $0) init import run"
    echo ''
    echo 'Commands:'
    echo ''
    echo '  install   - create virtual environments and install dependencies'
    echo '  uninstall - uninstall all dependencies in the virtual environments'
    echo '              NOTE: install / uninstall cannot be combined with other commands'
    echo ''
    echo '  init      - initializes the database'
    echo '  run       - runs the development server'
    echo "  index     - initializes the search index"
    echo '  test      - runs all tests'
    echo '  env       - shows all customizable environment variables'
    echo ' '
    echo "  import    - imports the data fixture JSON_DATA_FIXTURE=$JSON_DATA_FIXTURE"
    echo "  dump      - dumps data as JSON_DATA_FIXTURE=$JSON_DATA_FIXTURE"
    echo "  delete    - removes the sqlite database DATABASE_NAME=$DATABASE_NAME"
    echo ''
    echo "  pg_drop   - drops postgres DATABASE_NAME=$DATABASE_NAME"
    echo "  pg_create - creates postgres DATABASE_NAME=$DATABASE_NAME"
    echo "  pg_import file.gz - imports the gzipped filename into postgres DATABASE_NAME=$DATABASE_NAME"
    echo ''
    echo "Use environment variables to customize settings. See the docs."
    echo ' '
    echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
    echo "DATABASE_NAME=$DATABASE_NAME"
    echo ''
    exit
fi


export VIRTUAL_ENV_DISABLE_PROMPT=1

if [ "$1" = "install" ]; then
	set -ue  # stop on errors or missing environment variables.

	echo ""
	echo "==================== Installing reader-env ===================="
	virtualenv reader-env -p /usr/bin/python2.7
	(
		cd reader-env
		. bin/activate
		pip install --upgrade -r requirements/base.txt
		deactivate
	)

	echo ""
	echo "==================== Installing writer-env ===================="
	virtualenv writer-env -p /usr/bin/python3
	(
		cd writer-env
		. bin/activate
		pip install --upgrade -r requirements.txt
		deactivate
	)

	exit
fi

if [ "$1" = "uninstall" ]; then
	set -ue  # stop on errors or missing environment variables.

	echo ""
	echo "==================== Uninstalling reader-env ===================="
	(
		cd reader-env
		. bin/activate
		pip freeze | xargs pip uninstall -y
	)

	echo ""
	echo "==================== Uninstalling writer-env ===================="
	(
		cd writer-env
		. bin/activate
		pip freeze | xargs pip uninstall -y
	)

	exit
fi


# Active environment
cd ./reader-env
VIRTUAL_ENV_DISABLE_PROMPT=1 source ./bin/activate
cd ./project-basedir

# Set defaults for environment variables.

if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE=biostar.settings.base
fi

if [ -z "$JSON_DATA_FIXTURE" ]; then
   export JSON_DATA_FIXTURE="./reader-env/django-basedir/import/default-fixture.json.gz"
fi

if [ -z "$DATABASE_NAME" ]; then
   export DATABASE_NAME="live/biostar.db"
fi

if [ -z "$BIOSTAR_HOSTNAME" ]; then
   export BIOSTAR_HOSTNAME="www.lvh.me:8080"
fi

if [ -z "$PYTHON" ]; then
   export PYTHON="python -W ignore"
fi


# after this point stop on errors or missing environment variables.
set -ue

VERBOSITY=1


while (( "$#" )); do

    if [ "$1" = "delete" ]; then
        echo "*** Deleting the sqlite database"
        $PYTHON manage.py delete_database --settings=$DJANGO_SETTINGS_MODULE
    fi

    if [ "$1" = "pg_drop" ]; then
        echo "*** Dropping the $DATABASE_NAME=$DATABASE_NAME!"
        dropdb -i $DATABASE_NAME
    fi

    if [ "$1" = "pg_create" ]; then
        # creates the PG database
        echo "*** Creating postgresql database DATABASE_NAME=$DATABASE_NAME"
        createdb $DATABASE_NAME -E utf8 --template template0
    fi

    if [ "$1" = "pg_import" ]; then
        echo "*** Importing into DATABASE_NAME=$DATABASE_NAME"
        gunzip -c $2 | psql $DATABASE_NAME
    fi

    if [ "$1" = "pg_dump" ]; then
        echo "*** Dumping the $DATABASE_NAME database."
        $PYTHON manage.py biostar_pg_dump -v $VERBOSITY --settings=$DJANGO_SETTINGS_MODULE
    fi

    if [ "$1" = "run" ]; then
        echo "*** Run the development server with $DJANGO_SETTINGS_MODULE and DATABASE_NAME=$DATABASE_NAME"
        $PYTHON manage.py runserver $BIOSTAR_HOSTNAME --settings=$DJANGO_SETTINGS_MODULE
    fi

	if [ "$1" = "waitress" ]; then
        echo "*** Run a waitress server with $DJANGO_SETTINGS_MODULE and DATABASE_NAME=$DATABASE_NAME"
        waitress-serve --port=8080 --call biostar.wsgi:white
    fi

   	if [ "$1" = "testdeploy" ]; then
        echo "*** deploys to the test site"
        fab -f conf/fabs/fabfile.py test_site pull restart
    fi

    if [ "$1" = "init" ]; then
        echo "*** Initializing server on $BIOSTAR_HOSTNAME with $DJANGO_SETTINGS_MODULE"
        echo "*** Running all tests"
        #$PYTHON manage.py test --noinput -v $VERBOSITY --settings=$DJANGO_SETTINGS_MODULE
        $PYTHON manage.py syncdb -v $VERBOSITY --noinput --settings=$DJANGO_SETTINGS_MODULE

        $PYTHON manage.py migrate  biostar.apps.users --settings=$DJANGO_SETTINGS_MODULE
        $PYTHON manage.py migrate  biostar.apps.posts --settings=$DJANGO_SETTINGS_MODULE
        $PYTHON manage.py migrate  --settings=$DJANGO_SETTINGS_MODULE
        $PYTHON manage.py initialize_site --settings=$DJANGO_SETTINGS_MODULE

        $PYTHON manage.py collectstatic -v $VERBOSITY --noinput --settings=$DJANGO_SETTINGS_MODULE

    fi

    # Produce the environment variables recognized by Biostar.
    if [ "$1" = "test" ]; then
        echo "*** Running all tests"
        $PYTHON manage.py test --noinput --failfast -v $VERBOSITY --settings=$DJANGO_SETTINGS_MODULE
    fi

    # Produce the environment variables recognized by Biostar.
    if [ "$1" = "env" ]; then
        $PYTHON -m biostar.settings.base
    fi

    if [ "$1" = "import" ]; then
        echo "*** Importing json data from $JSON_DATA_FIXTURE"
        $PYTHON manage.py loaddata $JSON_DATA_FIXTURE --settings=$DJANGO_SETTINGS_MODULE
    fi

    if [ "$1" = "dump" ]; then
        echo "*** Dumping json data into $JSON_DATA_FIXTURE"
        $PYTHON manage.py dumpdata users posts messages badges planet --settings=$DJANGO_SETTINGS_MODULE | gzip > $JSON_DATA_FIXTURE
    fi

    if [ "$1" = "index" ]; then
        echo "*** Indexing site content"
        $PYTHON manage.py rebuild_index --noinput --settings=$DJANGO_SETTINGS_MODULE
    fi

    if [ "$1" = "update_index" ]; then
        echo "*** Updating site index"
        $PYTHON manage.py update_index --age 1 --settings=$DJANGO_SETTINGS_MODULE
    fi

    if [ "$1" = "import_biostar1" ]; then
        echo "*** Migrating from Biostar 1"
        echo "*** BIOSTAR_MIGRATE_DIR=$BIOSTAR_MIGRATE_DIR"
        $PYTHON manage.py import_biostar1 -u -p -x
    fi


shift
done
