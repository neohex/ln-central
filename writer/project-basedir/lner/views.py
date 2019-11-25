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
from common import util
from common import lnclient


logger = util.getLogger("lner.views")


class LightningNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows lightning nodes to be viewed
    """
    queryset = LightningNode.objects.all()
    serializer_class = LightningNodeSerializer


class LightningInvoiceList(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def get(self, request, format=None):
        node = LightningNode.objects.get(id=request.GET["node_id"])
        invoice = lnclient.addinvoice(request.GET["memo"], node.rpcserver, mock=settings.MOCK_LN_CLIENT)

        serializer = LightningInvoiceSerializer(invoice, many=False)  # re-serialize

        return Response(serializer.data)
