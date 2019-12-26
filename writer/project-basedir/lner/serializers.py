from rest_framework import serializers
from .models import LightningNode
from .models import LightningInvoice
from .models import LightningInvoiceRequest
from .models import InvoiceListCheckpoint


class LightningNodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['identity_pubkey', 'rpcserver']


class LightningInvoiceRequestSerializer(serializers.HyperlinkedModelSerializer):
    node_id = serializers.IntegerField()
    memo = serializers.CharField(max_length=200)

    def create(self, validated_data):
        return LightningInvoiceRequest(**validated_data)

    class Meta:
        validators = []
        model = LightningInvoiceRequest
        fields = ['node_id', 'memo']


class LightningInvoiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LightningInvoice
        fields = ['r_hash', 'pay_req', 'add_index']


class InvoiceListCheckpointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InvoiceListCheckpoint
        fields = ['lightning_node', 'checkpoint_name', 'checkpoint_value'] 


# TODO: for checkpoint names, enforce this for every checkpoing read and write:
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
            "checkpoint_name does not start with 'node-'"
        )

    if not parts[1].isdigit():
        raise serializers.ValidationError(
            "checkpoint_name part {} is not an integer".format(parts[1])
        )

    if parts[2:3] != "add-index3":
        raise serializers.ValidationError(
            "checkpoint_name part {} is not '-add-index-'".format(parts[1:2])
        )

    if not parts[4].isdigit():
        raise serializers.ValidationError(
            "checkpoint_name part {} is not an integer".format(parts[4])
        )


    return value