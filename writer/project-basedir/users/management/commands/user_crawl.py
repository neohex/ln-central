__author__ = 'ialbert'

from django.core.management import call_command
from django.conf import settings
from django.db import connection, transaction
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
from common.log import logger

from users.models import User
from users.management.awards import create_user_award
from users.management.awards import init_awards

import random
import os

os.environ['DJANGO_COLORS'] = 'nocolor'

class Command(BaseCommand):
    help = 'Performs actions on users'


    def add_arguments(self, parser):
        parser.add_argument('--award', action='store_true', help='goes over the users and attempts to create awards')


    def handle(self, *args, **options):

        if options['award']:
            crawl_awards()

def crawl_awards():
    init_awards()

    ids = [ u[0] for u in User.objects.all().values_list("id") ]

    # random.shuffle(ids)
    # ids = ids[:100]

    for pk  in ids:
        user = User.objects.get(pk=pk)
        create_user_award(user=user)
