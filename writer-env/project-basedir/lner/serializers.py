from rest_framework import serializers
from .models import LightningNode

class LightningNodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LightningNode
        fields = ['identity_pubkey']
