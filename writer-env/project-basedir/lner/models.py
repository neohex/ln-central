from django.db import models

class LightningNode(models.Model):
    identity_pubkey = models.CharField(verbose_name='LN Identity PubKey', db_index=True, max_length=255, unique=True)
