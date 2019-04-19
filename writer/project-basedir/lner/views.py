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
        if settings.MOCK_LN_CLIENT:
            invoice = [
                {
                    "r_hash": "48452417b7d351bdf1ce493521ffbc07157c68fd9340ba2aeead0c29899fa4b4",
                    "pay_req": "lnbc3u1pwfapdepp5fpzjg9ah6dgmmuwwfy6jrlauqu2hc68ajdqt52hw45xznzvl5j6qdqydp5scqzysdhdt9dngs8vw5532tcwnjvazn75cevfzz5r4drla8uvqlkt5u63nu5lrsa4s2q4rwmfe93yt7gavhrv3aq8rx3u842spdkwzhzketgsqv9zemq",
                    "add_index": 11
                 }
            ]
        else:
            invoice = [lnclient.addinvoice(request.GET["memo"])]

        serializer = LightningInvoiceSerializer(invoice, many=True)  # re-serialize
        return Response(serializer.data)
