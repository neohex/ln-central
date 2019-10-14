__author__ = 'ialbert'
from django.conf import settings
import hmac, logging, re
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from biostar.apps.users.models import User, Profile
from biostar import const
from django.core.cache import cache
from biostar.apps.posts.models import Post, Vote
from biostar.apps.messages.models import Message

from collections import defaultdict
from biostar.awards import create_user_award, check_user_profile

logger = logging.getLogger(__name__)


def get_ip(request):
    ip1 = request.META.get('REMOTE_ADDR', '')
    ip2 = request.META.get('HTTP_X_FORWARDED_FOR', '').split(",")[0].strip()
    ip = ip1 or ip2 or '0.0.0.0'
    return ip


ANON_USER = "anon-user"


class Visit(object):
    """
    Sets visit specific parameters on objects.
    """

    def process_request(self, request, weeks=settings.COUNT_INTERVAL_WEEKS):
        global ANON_USER
        pass
