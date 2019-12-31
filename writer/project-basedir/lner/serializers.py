from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import IntegerField
from rest_framework.serializers import CharField
from .models import LightningNode
from .models import LightningInvoice
from .models import LightningInvoiceRequest
from .models import InvoiceListCheckpoint
from common import validators


class LightningNodeSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['identity_pubkey', 'rpcserver']


class LightningInvoiceRequestSerializer(HyperlinkedModelSerializer):
    node_id = IntegerField()
    memo = CharField(max_length=200)

    def create(self, validated_data):
        return LightningInvoiceRequest(**validated_data)

    class Meta:
        validators = []
        model = LightningInvoiceRequest
        fields = ['node_id', 'memo']


class LightningInvoiceSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = LightningInvoice
        fields = ['r_hash', 'pay_req', 'add_index']


class InvoiceListCheckpointSerializer(HyperlinkedModelSerializer):
    checkpoint_name = CharField(validators=[validators.validate_checkpoint_name])
    class Meta:
        model = InvoiceListCheckpoint
        fields = ['lightning_node', 'checkpoint_name', 'checkpoint_value'] 