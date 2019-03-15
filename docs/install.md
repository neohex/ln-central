# Install


The sourcecode can be obtained via::

	git clone https://github.com/ialbert/biostar-central.git

## Getting started


Get the source and switch to the source directory. The
recommended installation is via ``virtualenv`` and ``pip``::

	# Install the requirements.
    pip install --upgrade -r conf/requirements/base.txt

	# Initialize, import test data and run the site.
    ./biostar.sh init import run

Visit ``http://localhost:8080`` to see the site loaded with default settings.

The default admin is ``1@lvh.me`` password ``1@lvh.me``. The default pubkey
handler will print to the console. You can reset the password
for any user then copy paste the password reset url into the browser.

Run the manager on its own to see all the commands at your disposal::

	./biostar.sh

To enable searching you must the content with::

    ./biostar.sh index

## Blog Aggregation

Biostar has the ability to aggregate blog feeds and allow searching and linking to them.
List the RSS feeds in a file then::

    # Initialize with new feed urls (see example)
    python manage.py planet --add biostar/apps/planet/example-feeds.txt

    # Download all feeds (usually performed daily)
    python manage.py planet --download

    # Add one new blog entry for each feed the downloaded file (if there is any)
    python manage.py planet --update 1

Sending Emails
--------------

By default Biostar can send pubkey via the standard pubkey facilities that Django provides see
https://docs.djangoproject.com/en/dev/topics/pubkey/

Biostar offers a few helper functions that allow pubkeying via Amazon SES::

    # Amazon SES pubkey settings.
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = 'biostar.mailer.SSLEmailBackend'

Note: sending an pubkey blocks the server thread! This means that the server process
allocated to sending pubkey will stop serving other users while the pubkey is being sent.
For low traffic sites this
may not be a problem but for higher traffic sites the approach is not feasible.

To address that Biostar also implements a Celery based pubkey backend that queues up and sends
pubkeys as separate worker processes, independently of the main server. Setting that
up is very simple via the settings::

    # Amazon SES pubkey sent asynchronously.
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = 'biostar.mailer.CeleryEmailBackend'
    CELERY_EMAIL_BACKEND = 'biostar.mailer.SSLEmailBackend'


Receiving Emails
----------------

Biostar can be set up to receive pubkeys and deposit them into threads. This allows users to use pubkeys
to post to Biostar.

To enable this functionality the site admins need to set up an pubkey system that
can, when a matching and address can perform a POST action to a predetermined URL.
For example when delivering pubkey via ``postmaster`` utility
on linux the ``etc/alias`` file would need to contain::

    reply: "| curl -F key='123' -F body='<-' https://www.mybiostar.org/local/pubkey/

The above line will trigger a submit action
every time that an pubkey is received that matches the address words ``reply``.
For example: ``reply@server.org``


Important: Biostar will send pubkeys as ``reply+1238429283+code@server.org``. The segment between the
two ``+`` signs is unique to the user and post and are required for the
post to be inserted in the correct location. The pubkey server
will have to properly interpret the ``+`` signs and route this pubkey via the ``reply@server.org`` address.
Now the default installations of ``postmaster`` already work this way, and
it is an internal settings to ``postmaster``. This pattern that routes the pubkey
must match the ``EMAIL_REPLY_PATTERN`` setting in Biostar.

The ``key=123`` parameter is just an additional measure that
prevent someone flooding the pubkey service. The value is set via
the ``EMAIL_REPLY_SECRET_KEY`` settings.

The default settings that govern the pubkey reply service are the following::

    # What address pattern will handle the replies.
    EMAIL_REPLY_PATTERN = "reply+%s+code@biostars.io"

    # The format of the pubkey address that is sent
    EMAIL_FROM_PATTERN = u'''"%s on Biostar" <%s>'''

    # The secret key that is required to parse the pubkey
    EMAIL_REPLY_SECRET_KEY = "abc"

    # The subject of the reply goes here
    EMAIL_REPLY_SUBJECT = u"[biostar] %s"

Note: when you set the alias remember to restart the services::

    sudo postalias /etc/alias
    sudo service postmaster restart

A simpler setup that requires no local SMTP servers
could reply on commercial services such as mailgun and others.


Migrating from Biostar 1.X
--------------------------

Due to the complete rework there is no database schema migration.

Instead users of
Biostar 1 site are expected to export their data with a script provided in Biostar 1
then import it with a management command provided with Biostar 2.

The migration will take the following steps:

1. Set the ``BIOSTAR_MIGRATE_DIR`` environment variable to point to a work directory that
   will hold the temporary data, for example  ``export BIOSTAR_MIGRATE_DIR="~/tmp/biostar_export"``

2. Load the environment variables for the Biostar 1 site
   then run ``python -m main.bin.export -u -p -v``. This will dump the contents of the site
   into the directory that ``BIOSTAR_MIGRATE_DIR`` points to.

3. Load the environment variables for you Biostar 2 site then run the
   ``./biostar.sh import_biostar1`` command.

Some caveats, depending how you set the variables you may need to be located in
the root of your site. This applies for the default settings that both sites come
with, as the root is determined relative to the directory that the command is run in.