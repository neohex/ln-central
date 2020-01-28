import datetime
import random
import hashlib
from django.utils.timezone import utc

def now():
    """
    TODO: check if this is equivalent to
                from django.utils import timezone
                timezone.now()
          if so then replace all calls with timezone.now()
    """

    return datetime.datetime.utcnow().replace(tzinfo=utc)

def unixtime_to_datetime(unixtime):
    return datetime.datetime.utcfromtimestamp(unixtime).replace(tzinfo=utc)

def make_uuid(size=None):
    "Returns a unique id"
    x = random.getrandbits(256)
    u = hashlib.md5(str(x).encode('utf-8')).hexdigest()
    u = u[:size]
    return u

def always_true(*args, **kwargs):
    "A helper we can substitue into any conditional function call"
    return True

def test():
    pass
