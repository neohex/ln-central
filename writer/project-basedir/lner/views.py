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


class CreateLightningInvoiceViewSet(viewsets.ModelViewSet):
    """
    Create a new lightning invoice
    """
    queryset = []
    serializer_class = LightningInvoiceRequestSerializer

    def create(self, request):
        node = LightningNode.objects.get(id=request.POST["node_id"])
        invoice = lnclient.addinvoice(
            request.POST["memo"],
            node.rpcserver,
            amt=settings.PAYMENT_AMOUNT,
            mock=settings.MOCK_LN_CLIENT
        )

        serializer = LightningInvoiceSerializer(data=invoice, many=False)  # re-serialize
        serializer.is_valid(raise_exception=True)  # validate data going into the database

        return Response(serializer.validated_data)

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
