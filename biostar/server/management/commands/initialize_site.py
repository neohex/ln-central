from __future__ import print_function, unicode_literals, absolute_import, division
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os, logging
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage

from django.core.exceptions import ImproperlyConfigured
from optparse import make_option

logger = logging.getLogger(__name__)

def abspath(*args):
    """Generates absolute paths"""
    return os.path.abspath(os.path.join(*args))

class Command(BaseCommand):
    help = 'Initializes content in Biostar'

    def handle(self, *args, **options):
        from biostar import awards
        init_flatpages()
        init_admin()
        init_domain()
        awards.init_awards()

def init_flatpages():
    # list for the flatpages
    names = "faq about help policy api".split()
    site = Site.objects.get_current()
    for name in names:
        url = "/info/%s/" % name
        page = FlatPage.objects.filter(url=url, sites=site)
        if not page:
            path = abspath(settings.FLATPAGE_IMPORT_DIR, name)
            path = "%s.html" % path
            if not os.path.isfile(path):
                logger.error("cannot find flatpage %s" % path)
                continue
            content = file(path).read()
            page = FlatPage.objects.create(url=url, content=content, title=name.capitalize())
            page.sites.add(site)
            page.save()
            logger.info("added flatpage for url: %s" % url)

def init_admin():
    # Add the admin user if it is not present.
    from biostar.apps.users.models import User

    admin = User.objects.filter(id=1)

def init_domain():
    # Initialize to the current site if it is not present.
    from django.contrib.sites.models import Site

    site = Site.objects.get_current()
    if site.domain != settings.SITE_DOMAIN:
        site.name = settings.SITE_NAME
        site.domain = settings.SITE_DOMAIN
        site.save()
        logger.info("adding site=%s, name=%s, domain=%s" % (site.id, site.name, site.domain))

    # Initialize media folder
    for path in (settings.EXPORT_DIR, settings.MEDIA_ROOT):
        if not os.path.isdir(path):
            os.mkdir(path)
