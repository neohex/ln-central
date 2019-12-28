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