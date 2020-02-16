import re
import sys
import json

from django.core.exceptions import ValidationError
from common.log import logger


def validate_checkpoint_name(value):
    """
    Check that checkpoint_name is one of the valid formats:
      - 'global-offset'
      - 'node-[0-9]+-add-index-[0-9]+'
    """
    if value in ["global-offset"]:
        return value

    parts = value.split("-")
    if len(parts) != 5:
        raise ValidationError(
            "checkpoint_name does not consist of 5 parts"
        )

    if parts[0] != "node":
        raise ValidationError(
            "checkpoint_name does not start with 'node'"
        )

    if not parts[1].isdigit():
        raise ValidationError(
            "checkpoint_name part {} is not an integer".format(parts[1])
        )

    if parts[2:4] != ["add", "index"]:
        raise ValidationError(
            "checkpoint_name part {} is not 'add-index'".format(parts[2:4])
        )

    if not parts[4].isdigit():
        raise ValidationError(
            "checkpoint_name part {} is not an integer".format(parts[4])
        )


    return value


def validate_signable_field(value, key="unknown", no_auto_correct=False):
    """
    if no_auto_correct is set to True then instead of returning
    corrected version, a ValidationError will be raise
    """

    if value is None:
        return None

    new_value = value.strip(" \t\n\r\x0b\f")
    if new_value != value:
        # since we're asking the user to sign text via CLI
        # it's very easy to accidentally add an extra newline or space
        # and change the signature
        if no_auto_correct:
            raise ValidationError(
                (
                    "memo for key {} has a value with leading or triling whitespace characters: {}"
                ).format(key, value)
            )
        else:
            return new_value
    return value

def pre_validate_signature(signature):
    if re.match('^[a-z0-9]+$', signature):
        return signature

    if re.match('^[a-z0-9"}{: \r\n,]+$', signature):
        try:
            parsed_signature = json.loads(signature)
        except ValueError as msg:
            logger.debug("Signature JSON is invalid: '{}' the error was {}".format(signature, msg))
            raise ValidationError("Signature JSON is invalid")

        if "signature" not in parsed_signature:
            raise ValidationError("Signature JSON does look like the output for lncli signmessage")

        if re.match('^[a-z0-9]+$', parsed_signature["signature"]):
            return parsed_signature["signature"]

    raise ValidationError("Signature is not JSON or has other characters then lower-case letters and numbers")

def validate_memo(memo, no_auto_correct=False):
    new_memo = {}

    for key, value in memo.items():
        # TODO: Remove version check after reader is migrated to Python 3
        if sys.version_info >= (3, 0):
            if not isinstance(key, str):
                raise ValidationError(("memo for key {} is not a string").format(repr(key)))
        else:
            if not isinstance(key, basestring):
                raise ValidationError(("memo for key {} is not a string").format(repr(key)))

        if re.match('^[a-z_]+$', key) is None:
            raise ValidationError(
                (
                    "memo for key {} is not valid, should only contain letters and underscores"
                ).format(key)
            )

        new_memo[key] = value

    # TODO: check types of other fields

    # signable fields that are strings
    signable_fields = ["content"]
    if "parent_post_id" in memo:
        if "title" in memo:
            raise ValidationError("memo with parent_post_id should not have titles")
    else:
        signable_fields += ["title"]

    for key in signable_fields:
        value = memo[key]
        new_value = validate_signable_field(value, key=key, no_auto_correct=no_auto_correct)
        new_memo[key] = new_value

    return new_memo
