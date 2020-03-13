__author__ = 'ialbert'

from django.core.management import call_command
from django.conf import settings
from django.db import connection, transaction
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
from common.log import logger

from posts.models import Post
from posts.models import Vote
from users.models import User
from badges.models import Award

from users.management.awards import create_user_award
from users.management.awards import init_awards

import random
import os

os.environ['DJANGO_COLORS'] = 'nocolor'

class Command(BaseCommand):
    help = 'Goes thru all posts and prompts if they should be marked as fake test data'

    def handle(self, *args, **options):
        mark_fake_test_data()


def yesno(question):
    res = input("{} (Enter y/n) ".format(question)).lower()

    if res not in {"y", "n"}:
        print('Please type "y" or "n" ')
        res = yesno(question)

    return res == "y"

def mark_fake_test_data():
    # Posts
    print("Posts:")
    for p in Post.objects.all().exclude(is_fake_test_data=True).order_by('-creation_date'):
        print("id={}\tcreation_date={}\ttitle={}".format(p.id, p.creation_date, p.title))
        if yesno("Mark as fake?"):
            p.is_fake_test_data = True
            p.save()
            print("Marked post as fake test data!")

    # Users
    print("\nUsers:")
    for u in User.objects.exclude():
        if Post.objects.filter(author=u, is_fake_test_data=False):
            if u.is_fake_test_data:
                print("User (id={}\tpubkey={})".format(u.id, u.pubkey))
                u.is_fake_test_data = False
                u.save()
                print("User has real posts, marked user {} as real!".format(u.id))
        else:
            if not u.is_fake_test_data:
                print("User (id={}\tpubkey={})".format(u.id, u.pubkey))
                u.is_fake_test_data = True
                u.save()
                print("No real posts by user, marked user {} as fake test data!".format(u.id))


    # Votes
    print("\n\nVotes:")
    for v in Vote.objects.exclude(is_fake_test_data=True):
        if v.post.is_fake_test_data:
            print("Vote (id={})".format(v.id))
            v.is_fake_test_data = True
            v.save()
            print("Vote is for a fake test data post, marked vote {} as fake test data!".format(v.id))

    # Awards
    print("\n\nAwards:")
    for a in Award.objects.exclude(is_fake_test_data=True):
        if a.user.is_fake_test_data:
            print("Award (id={})".format(a.id))
            a.is_fake_test_data = True
            a.save()
            print("Award author is not real, marked award {} as fake test data!".format(a.id))

    # Update reply counts (in case some reply was marked as fake)
    print("\n\nUpdating reply counts!")
    for p in Post.objects.all().exclude(is_fake_test_data=True):
        p.save()
