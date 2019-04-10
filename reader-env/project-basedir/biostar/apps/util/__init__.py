import random, hashlib, json, base64, hmac
import binascii
import zlib
from datetime import datetime
from django.utils.timezone import utc


def serialize_memo(simple_obj):
    '''
    Lightning payment needs to encode website actions inside the
    invoice description field.

    Requirements:
    - simple_obj must be convertible to json
    
    TODO: check for serialized version not to exceed 600 bytes
    leaving some room as the final limit is 639 bytes.
    See https://blockfuse.io/blog/lightning-network-invoices/
    '''
    json_str = json.dumps(simple_obj)
    return binascii.b2a_base64(zlib.compress(json_str)).rstrip("\n")


def deserialize_memo(memo):
    '''
    Inverse of serialize_memo
    '''
    json_str = zlib.decompress(binascii.a2b_base64(memo))
    return json.loads(json_str)


def now():
    return datetime.utcnow().replace(tzinfo=utc)

def split_tags(text):
    "Splits tags by comma and applies a formatting on case"
    # Upper case
    def fixcase(w):
        w = w.strip()
        w = w.upper() if len(w) == 1 else w.lower()
        return w

    # Try splitting by comma
    words = text.split(",")

    # Change case as necessary.
    words = map(fixcase, words)

    # Remove empty
    words = filter(None, words)

    return words

def make_uuid(size=None):
    "Returns a unique id"
    x = random.getrandbits(256)
    u = hashlib.md5(str(x)).hexdigest()
    u = u[:size]
    return u

def encode(data, key):
    text = json.dumps(data)
    text = base64.urlsafe_b64encode(text)
    digest = hmac.new(key, text).hexdigest()
    return text, digest

def decode(text, digest, key):
    if digest != hmac.new(key, text).hexdigest():
        raise Exception("message does not match the digest")
    text = base64.urlsafe_b64decode(text)
    data = json.loads(text)
    return data

def always_true(*args, **kwargs):
    "A helper we can substitue into any conditional function call"
    return True