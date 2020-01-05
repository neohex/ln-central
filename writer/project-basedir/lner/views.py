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

from .models import LightningNode
from .models import LightningInvoice
from .models import LightningInvoiceRequest
from .models import InvoiceListCheckpoint
from .serializers import LightningNodeSerializer
from .serializers import LightningInvoiceSerializer
from .serializers import LightningInvoiceRequestSerializer
from .serializers import InvoiceListCheckpointSerializer
from common import log
from common import lnclient


logger = log.getLogger("lner.views")


class LightningNodeViewSet(viewsets.ModelViewSet):
    """
    List all available lightning nodes
    """
    queryset = LightningNode.objects.all()
    serializer_class = LightningNodeSerializer


class CreateLightningInvoiceError(Exception):
    pass

class CreateLightningInvoiceViewSet(viewsets.ModelViewSet):
    """
    Create a new lightning invoice
    """
    queryset = []
    serializer_class = LightningInvoiceRequestSerializer

    MAX_RETRIES = 3
    RETRY_SLEEP_SECONDS = 1

    def create(self, request, format=None, retry_addinvoice=False, retry_num=0):
        if retry_num >= CreateLightningInvoiceViewSet.MAX_RETRIES:
            raise CreateLightningInvoiceError(
                "Retry count exceeded: {}".format(retry_num)
            )

        node = LightningNode.objects.get(id=request.POST["node_id"])
        request_obj, created = LightningInvoiceRequest.objects.get_or_create(
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

            serializer = LightningInvoiceSerializer(data=invoice_stdout, many=False)  # re-serialize
            serializer.is_valid(raise_exception=True)  # validate data going into the database

            invoice_obj = LightningInvoice(
                lightning_invoice_request=request_obj,
                r_hash=serializer.validated_data.get("r_hash"),
                pay_req=serializer.validated_data.get("pay_req"),
                add_index=serializer.validated_data.get("add_index")
            )
            invoice_obj.save()
            return Response(serializer.validated_data)

        else:
            try:
                invoice_obj = LightningInvoice.objects.get(lightning_invoice_request=request_obj)
            except LightningInvoice.DoesNotExist:
                retry_num += 1
                time.sleep(CreateLightningInvoiceViewSet.RETRY_SLEEP_SECONDS)
                return self.create(request, format=format, retry_addinvoice=True, retry_num=retry_num)

            serializer = LightningInvoiceSerializer(invoice_obj)
            return Response(serializer.data)
        

class CheckPaymentViewSet(viewsets.ViewSet):
    """
    Check invoice to see if payment was setteled
    """

    lookup_field = 'checkpoint_name'
    lookup_value_regex = '[a-z0-9-]+'

    def retrieve(self, request, checkpoint_name):
        queryset = InvoiceListCheckpoint.objects.all()
        checkpoint = get_object_or_404(queryset, checkpoint_name=checkpoint_name)
        serializer = InvoiceListCheckpointSerializer(checkpoint, context={'request': request})

        return Response(serializer.data)
