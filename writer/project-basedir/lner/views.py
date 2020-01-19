import time

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework import mixins

from .models import LightningNode
from .models import Invoice
from .models import InvoiceRequest

from .serializers import LightningNodeSerializer
from .serializers import InvoiceSerializer
from .serializers import InvoiceRequestSerializer
from .serializers import CheckPaymentSerializer

from common import log
from common import lnclient


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
            # TODO: surface addinvoice timeout and other exceptions back to the user
            invoice_stdout = lnclient.addinvoice(
                request.POST["memo"],
                node.rpcserver,
                amt=settings.PAYMENT_AMOUNT,
                mock=settings.MOCK_LN_CLIENT
            )

            serializer = InvoiceSerializer(data=invoice_stdout, many=False)  # re-serialize
            serializer.is_valid(raise_exception=True)  # validate data going into the database

            invoice_obj = Invoice(
                invoice_request=request_obj,
                pay_req=serializer.validated_data.get("pay_req"),
            )
            invoice_obj.save()
            return Response(serializer.validated_data)

        else:
            try:
                invoice_obj = Invoice.objects.get(invoice_request=request_obj)
            except Invoice.DoesNotExist:
                retry_num += 1
                time.sleep(CreateInvoiceViewSet.RETRY_SLEEP_SECONDS)
                return self.create(request, format=format, retry_addinvoice=True, retry_num=retry_num)

            serializer = InvoiceSerializer(invoice_obj)
            return Response(serializer.data)

class CheckPaymentViewSet(viewsets.ModelViewSet):
    """
    Check invoice to see if payment was setteled
    """

    queryset = []
    serializer_class = CheckPaymentSerializer
    lookup_field = 'memo'
    lookup_value_regex = '[a-z0-9-]+'

    def get_queryset(self):
        memo = self.request.query_params.get("memo")

        invoice_request = get_object_or_404(InvoiceRequest, memo=memo)
        invoice = get_object_or_404(Invoice, invoice_request=invoice_request.pk)

        return [invoice]
