from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import IntegerField
from rest_framework.serializers import CharField
from .models import LightningNode
from .models import Invoice
from .models import InvoiceRequest
from common import validators


class LightningNodeSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['identity_pubkey', 'rpcserver']


class InvoiceRequestSerializer(HyperlinkedModelSerializer):
    node_id = IntegerField()
    memo = CharField(max_length=200)

    def create(self, validated_data):
        return InvoiceRequest(**validated_data)

    class Meta:
        validators = []
        model = InvoiceRequest
        fields = ['node_id', 'memo']


class InvoiceSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Invoice
        fields = ['r_hash', 'pay_req', 'add_index']  # TODO: only pay_req is what reader needs. Return only "pay_req" on retirev. Yet on create we need to have all fields.


class CheckPaymentSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Invoice
        fields = ['checkpoint_value', 'pay_req']
