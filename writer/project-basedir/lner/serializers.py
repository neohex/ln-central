from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import IntegerField
from rest_framework.serializers import CharField
from rest_framework.serializers import BooleanField

from django.conf import settings

from lner.models import LightningNode
from lner.models import Invoice
from lner.models import InvoiceRequest
from lner.models import VerifyMessageResult
from lner.models import PayAwardResult

from common import validators


class LightningNodeSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['id', 'node_name', 'node_key', 'rpcserver', 'qos_score', 'enabled', 'is_tor', 'connect_ip', 'connect_tor']


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
    node_id = IntegerField()

    class Meta:
        model = Invoice
        fields = ['node_id', 'r_hash', 'pay_req', 'add_index']  # TODO: only pay_req is what reader needs. Return only "pay_req" on retirev. Yet on create we need to have all fields.


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


class PayAwardResponseSerializer(HyperlinkedModelSerializer):
    payment_successful = BooleanField()
    failure_message =  CharField(
        max_length=255,
        default=""
    )

    class Meta:
        model = PayAwardResult
        fields = ['payment_successful', 'failure_message']
