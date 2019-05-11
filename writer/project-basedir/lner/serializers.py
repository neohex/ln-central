from rest_framework import serializers
from .models import LightningNode
from .models import LightningInvoice
from .models import InvoiceListCheckpoint


class LightningNodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['identity_pubkey', 'rpcserver']


class LightningInvoiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LightningInvoice
        fields = ['r_hash', 'pay_req', 'add_index']

class InvoiceListCheckpointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InvoiceListCheckpoint
        fields = ['lightning_node', 'checkpoint_name', 'add_index']