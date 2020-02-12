from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import IntegerField
from rest_framework.serializers import CharField
from rest_framework.serializers import BooleanField

from django.conf import settings

from lner.models import LightningNode
from lner.models import Invoice
from lner.models import InvoiceRequest
from lner.models import VerifyMessageResult
from common import validators


class LightningNodeSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['id', 'identity_pubkey', 'rpcserver']


class InvoiceRequestSerializer(HyperlinkedModelSerializer):
    node_id = IntegerField()
    memo = CharField(max_length=settings.MAX_MEMO_SIZE)

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
        fields = ['checkpoint_value', 'pay_req', 'performed_action_type', 'performed_action_id']

class VerifyMessageResponseSerializer(HyperlinkedModelSerializer):
    memo = CharField(max_length=settings.MAX_MEMO_SIZE)
    identity_pubkey = CharField(max_length=255)
    valid = BooleanField()

    class Meta:
        model = VerifyMessageResult
        fields = ['memo', 'valid', 'identity_pubkey']
