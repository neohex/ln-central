from django.shortcuts import render
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
from .serializers import LightningNodeSerializer
from .serializers import LightningInvoiceSerializer
from .serializers import LightningInvoiceRequestSerializer
from common import util
from common import lnclient


logger = util.getLogger("lner.views")


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

    def create(self, request, format):
        node = LightningNode.objects.get(id=request.POST["node_id"])
        invoice = lnclient.addinvoice(request.POST["memo"], node.rpcserver, mock=settings.MOCK_LN_CLIENT)

        serializer = LightningInvoiceSerializer(invoice, many=False)  # re-serialize

        return Response(serializer.data)
