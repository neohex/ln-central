from django.shortcuts import render

from rest_framework import viewsets
from .models import LightningNode
from .models import LightningInvoice
from .serializers import LightningNodeSerializer

class LightningNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows lightning nodes to be viewed
    """
    queryset = LightningNode.objects.all()
    serializer_class = LightningNodeSerializer


class LightningInvoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows lightning invoces to be added
    """
    queryset = LightningInvoice.objects.all()
    serializer_class = LightningNodeSerializer