import json, base64, hmac
import binascii
import zlib

from django.conf import settings

class JsonUtilException(Exception):
    pass


class MemoTooLarge(Exception):
    pass


def serialize_memo(simple_obj):
    '''
    Lightning payment needs to encode website actions inside the
    invoice description field.

    Requirements:
    - simple_obj must be convertible to json
    - after converting to json and compressing, there is a limit on bytes size
    
    Check for serialized version not to exceed 1000 bytes (MAX_MEMO_SIZE)

    See https://github.com/lightningnetwork/lnd/commit/b264ba198fc362505616c7b8e2decb8a62d5797d#diff-9f84ce21f17bb10010b2d2b19cb17e3cR39
    '''
    json_str = json.dumps(simple_obj)
    serialized = binascii.b2a_base64(zlib.compress(json_str)).rstrip("\n")

    assert "_" not in settings.FRIENDLY_PREFIX, "cannot have spaces in FRIENDLY_PREFIX"
    serialized = "{}_{}".format(settings.FRIENDLY_PREFIX, serialized)

    if len(serialized) > settings.MAX_MEMO_SIZE:
        raise MemoTooLarge(
            "memo too large: {} bytes (maxsize={}})".format(
                len(serialized),
                settings.MAX_MEMO_SIZE
            )
        )

    return serialized


def deserialize_memo(memo):
    '''
    Inverse of serialize_memo
    '''

    # drop FRIENDLY_PREFIX, which is the first word, we don't check
    # what the actual word is because FRIENDLY_PREFIX can change
    if "_" not in memo:
        raise JsonUtilException("Expecting at least one _ in memo")

    memo = memo.split("_", 1)[1]

    try:
        memo64 = binascii.a2b_base64(memo)
    except Exception as e:
        raise JsonUtilException("Cannot convert memo to base64: {}".format(e))

    try:
        json_str = zlib.decompress(memo64)
    except Exception as e:
        raise JsonUtilException("Cannot decomress memo: {}".format(e))

    try:
        json_str = json_str.decode('utf-8')
    except Exception as e:
        raise JsonUtilException("Cannot decode memo to utf-8: {}".format(e))

    try:
        obj = json.loads(json_str)
    except Exception as e:
        raise JsonUtilException("Cannot parse JSON from memo: {}".format(e))

    return obj


def encode(data, key):
    text = json.dumps(data)
    text = base64.urlsafe_b64encode(text)
    digest = hmac.new(key, text).hexdigest()
    return text, digest

def decode(text, digest, key):
    if digest != hmac.new(key, text).hexdigest():
        raise JsonUtilException("message does not match the digest")

    text = base64.urlsafe_b64decode(text)
    data = json.loads(text)
    return data
