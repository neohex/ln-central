__author__ = 'ialbert'
from django.conf import settings
from django.core.cache import cache
from biostar.apps.users.models import User
from biostar.apps.posts.models import Post, Vote
from biostar.apps.badges.models import Award
from biostar.apps import util

from common import const
from biostar import VERSION

from datetime import timedelta
from math import pow, e, log
from random import random

LOG2 = log(2)
CACHE_TIMEOUT = settings.CACHE_TIMEOUT


def get_recent_votes():
    # TODO: this should be done in the background and periodic intervals, not for every request

    votes = Vote.objects.filter(post__status=Post.OPEN).select_related("post").order_by("post__id")

    # poor man's DISTINCT ON (because it's only supported in PostgreSQL)
    distinct_votes = []
    prev_vote = None
    for v in votes:
        if prev_vote and v.post.id != prev_vote.post.id:
            distinct_votes.append(v)
        prev_vote = v

    distinct_votes.sort(key=lambda x: x.date, reverse=True)

    return distinct_votes[:settings.RECENT_VOTE_COUNT]



def get_recent_users():
    users = User.objects.all().select_related("profile").order_by("-profile__last_login")[:settings.RECENT_USER_COUNT]
    return users


def get_recent_awards():
    awards = Award.objects.all().select_related("user", "badge")
    awards = awards.order_by("-date")[:6]
    return awards


def get_recent_replies():
    posts = Post.objects.filter(type__in=(Post.ANSWER, Post.COMMENT), root__status=Post.OPEN).select_related(("author"))
    posts = posts.order_by("-creation_date")
    posts = posts[:settings.RECENT_POST_COUNT]
    return posts


TRAFFIC_KEY = "traffic"


def get_traffic(minutes=60):
    "Obtains the number of actions taken in the last X minutes"

    return "_Unknown_number_of_"


def banner_trigger(request, half=settings.HALF_LIFE):
    # user = request.user
    # if user.is_anonymous() or user.profile.opt_in:
    #     return True
    # level = pow(e, -LOG2 * user.score/half) + 0.01
    # rand = random()
    # return rand <= level
    return True

def shortcuts(request):
    # These values will be added to each context

    context = {
        "SITE_STYLE_CSS": settings.SITE_STYLE_CSS,
        "SITE_LOGO": settings.SITE_LOGO,
        "SITE_NAME": settings.SITE_NAME,
        "CATEGORIES": settings.CATEGORIES,
        "BUILD_HASH": VERSION['build_hash'],
        "BUILD_TIME": VERSION['build_time'],
        "SERVER_START_TIME": VERSION['server_start_time'],
        "TRAFFIC": get_traffic(),
        'RECENT_REPLIES': get_recent_replies(),
        'RECENT_VOTES': get_recent_votes(),
        "RECENT_USERS": get_recent_users(),
        "RECENT_AWARDS": get_recent_awards(),
        'USE_COMPRESSOR': settings.USE_COMPRESSOR,
        'SITE_ADMINS': settings.ADMINS,
        'TOP_BANNER': settings.TOP_BANNER,
        'BANNER_TRIGGER': banner_trigger(request),
    }

    return context
