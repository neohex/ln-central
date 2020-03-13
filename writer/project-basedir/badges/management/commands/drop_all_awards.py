from django.core.management.base import BaseCommand, CommandError

from common.log import logger

from badges.models import Award
from badges.models import Badge

import os

os.environ['DJANGO_COLORS'] = 'nocolor'

class Command(BaseCommand):
    help = 'Drops all awards'

    def handle(self, *args, **options):
        drop_all_awards()


def drop_all_awards():
    for a in Award.objects.all():
        a.delete()

    for b in Badge.objects.all():
        b.delete()
