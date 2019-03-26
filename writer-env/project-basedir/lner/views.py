from django.shortcuts import render

from rest_framework import viewsets
from .models import LightningNode
from .serializers import LightningNodeSerializer

class LightningNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows lightning nodes to be viewed
    """
    queryset = LightningNode.objects.all()
    serializer_class = LightningNodeSerializer
