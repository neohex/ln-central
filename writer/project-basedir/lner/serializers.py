from rest_framework import serializers
from .models import LightningNode
from .models import LightningInvoice
from .models import LightningInvoiceRequest
from .models import InvoiceListCheckpoint
from lner import validators


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
    checkpoint_name = serializers.CharField(validators=[validators.validate_checkpoint_name])
    class Meta:
        model = InvoiceListCheckpoint
        fields = ['lightning_node', 'checkpoint_name', 'checkpoint_value'] 