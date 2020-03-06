import time
import re

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.conf import settings
from django.db.models import Max

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework import mixins

from lner.models import LightningNode
from lner.models import Invoice
from lner.models import InvoiceRequest
from lner.models import VerifyMessageResult

from lner.serializers import LightningNodeSerializer
from lner.serializers import InvoiceSerializer
from lner.serializers import InvoiceRequestSerializer
from lner.serializers import CheckPaymentSerializer
from lner.serializers import VerifyMessageResponseSerializer

from common import log
from common import lnclient
from common import validators

from common.const import MEMO_RE


logger = log.getLogger("lner.views")


class LightningNodeViewSet(viewsets.ModelViewSet):
    """
    List all available lightning nodes
    """
    queryset = LightningNode.objects.all()
    serializer_class = LightningNodeSerializer


class CreateInvoiceError(Exception):
    pass

class CreateInvoiceViewSet(viewsets.ModelViewSet):
    """
    Create a new lightning invoice
    """
    queryset = []
    serializer_class = InvoiceRequestSerializer

    MAX_RETRIES = 3
    RETRY_SLEEP_SECONDS = 1

    def create(self, request, format=None, retry_addinvoice=False, retry_num=0):
        if retry_num >= CreateInvoiceViewSet.MAX_RETRIES:
            raise CreateInvoiceError(
                "Retry count exceeded: {}".format(retry_num)
            )

        node = LightningNode.objects.get(id=request.POST["node_id"])
        request_obj, created = InvoiceRequest.objects.get_or_create(
            lightning_node=node,
            memo=request.POST["memo"]
        )

        if created or retry_addinvoice:
            logger.info("New invoice request created: {}".format(request_obj))
            # InvoiceRequest just got created? do:
            #  1. addinvoice RPC to the node
            #  2. create Invoice

            if settings.MOCK_LN_CLIENT:
                invoice_stdout = {}

                invoice_stdout["pay_req"] = "FAKE"
                invoice_stdout["r_hash"] = "FAKE"

                if len(Invoice.objects.all()) == 0:
                    invoice_stdout["add_index"] = 1
                else:
                    # TODO: Mock mulitiple nodes. Currently Mock uses Invoice.objects.aggregate which ignores node.
                    invoice_stdout["add_index"] = Invoice.objects.aggregate(Max('add_index'))["add_index__max"] + 1

                serializer = InvoiceSerializer(data=invoice_stdout, many=False)  # re-serialize
                is_valid = serializer.is_valid(raise_exception=False)  # validate data going into the database

                invoice_obj = Invoice(
                    invoice_request=request_obj,
                    pay_req=serializer.validated_data.get("pay_req"),
                    r_hash=serializer.validated_data.get("r_hash"),
                    add_index=serializer.validated_data.get("add_index")
                )
                invoice_obj.save()
                return Response(serializer.validated_data)

            else:
                # TODO: surface addinvoice timeout and other exceptions back to the user
                invoice_stdout = lnclient.addinvoice(
                    request.POST["memo"],
                    node.rpcserver,
                    amt=settings.PAYMENT_AMOUNT,
                    expiry=settings.INVOICE_EXPIRY,
                )
                logger.info("Finished addinvoice on the node")

                if "payment_request" in invoice_stdout:
                    # lncli returns "payment_request" instead of "pay_req", probably since
                    # commit 8f5d78c875b8eca436f7ee2e86e743afee262386 (Dec 20 2019)  build+lncli: default to hex encoding for byte slices
                    invoice_stdout["pay_req"] = invoice_stdout["payment_request"]

                serializer = InvoiceSerializer(data=invoice_stdout, many=False)  # re-serialize
                is_valid = serializer.is_valid(raise_exception=False)  # validate data going into the database

                if not is_valid:
                    msg = "Output of addinvoice was not valid: errors={} stdout={}".format(serializer.errors, invoice_stdout)
                    logger.error(msg)
                    raise CreateInvoiceError(msg)

                invoice_obj = Invoice(
                    invoice_request=request_obj,
                    pay_req=serializer.validated_data.get("pay_req"),
                    r_hash=serializer.validated_data.get("r_hash"),
                    add_index=serializer.validated_data.get("add_index")
                )
                invoice_obj.save()
                logger.info("Saved results of addinvoice to DB")

                return Response(serializer.validated_data)

        else:
            logger.info("Invoice request already exists: {}".format(request_obj))
            try:
                invoice_obj = Invoice.objects.get(invoice_request=request_obj)
                logger.info("New invoice created: {}".format(invoice_obj))

            except Invoice.DoesNotExist:
                logger.info("Re-trying to create new invoice")
                retry_num += 1
                time.sleep(CreateInvoiceViewSet.RETRY_SLEEP_SECONDS)
                return self.create(request, format=format, retry_addinvoice=True, retry_num=retry_num)

            serializer = InvoiceSerializer(invoice_obj)


            return Response(serializer.data)


class CheckPaymentViewSet(viewsets.ModelViewSet):
    """
    Check invoice to see if payment was settled
    """

    queryset = []
    serializer_class = CheckPaymentSerializer

    def get_queryset(self):
        memo = self.request.query_params.get("memo")
        node_id = self.request.query_params.get("node_id")

        assert re.match(MEMO_RE, memo), "Got invalid memo {}".format(memo)

        invoice_request = get_object_or_404(InvoiceRequest, memo=memo, lightning_node_id=node_id)
        invoice = get_object_or_404(Invoice, invoice_request=invoice_request)

        return [invoice]



class VerifyMessageViewSet(viewsets.ModelViewSet):
    """
    Check message against a signature
    """

    queryset = []
    serializer_class = VerifyMessageResponseSerializer

    def get_queryset(self):
        memo = self.request.query_params.get("memo")
        sig = self.request.query_params.get("sig")

        assert memo is not None, "Missing a required field: memo"
        assert sig is not None, "Missing a required field: sig"

        sig = validators.pre_validate_signature(sig)

        node = LightningNode.objects.order_by("?").first()

        result_json = lnclient.verifymessage(msg=memo, sig=sig, rpcserver=node.rpcserver, mock=settings.MOCK_LN_CLIENT)
        pubkey = result_json["pubkey"]
        valid = result_json["valid"]

        verify_message_result = VerifyMessageResult(memo=memo, identity_pubkey=pubkey, valid=valid)

        return [verify_message_result]

