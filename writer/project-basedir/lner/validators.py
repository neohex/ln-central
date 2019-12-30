import re
from rest_framework import serializers

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
        raise serializers.ValidationError(
            "checkpoint_name does not consist of 5 parts"
        )

    if parts[0] != "node":
        raise serializers.ValidationError(
            "checkpoint_name does not start with 'node'"
        )

    if not parts[1].isdigit():
        raise serializers.ValidationError(
            "checkpoint_name part {} is not an integer".format(parts[1])
        )

    if parts[2:4] != ["add", "index"]:
        raise serializers.ValidationError(
            "checkpoint_name part {} is not 'add-index'".format(parts[2:4])
        )

    if not parts[4].isdigit():
        raise serializers.ValidationError(
            "checkpoint_name part {} is not an integer".format(parts[4])
        )


    return value


def validate_memo(memo):
    for key, value in memo.items():
        if not isinstance(key, str):
            raise serializers.ValidationError(("memo for key {} is not a string").format(key))

        if re.match('^[a-z_]+$', key) is None:
            raise serializers.ValidationError(
                (
                    "memo for key {} is not valid, should only contain letters and underscores"
                ).format(key)
            )

        if isinstance(value, str):
            if value.strip(" \t\n\r\x0b\f") != value:
                # since we're asking the user to sign text via CLI
                # it's very easy to accidently add an extra newline or space
                # and change the signiture
                raise serializers.ValidationError(
                    (
                        "memo for key {} has a value with leading or triling whitespace characters: {}"
                    ).format(key, value)
                )
