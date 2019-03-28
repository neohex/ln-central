from django.db import models

class LightningNode(models.Model):
    identity_pubkey = models.CharField(verbose_name='LN Identity Pubkey', db_index=True, max_length=255, unique=True)

class LightningInvoice(models.Model):
    pay_req = models.CharField(verbose_name='LN Invoice pay_req', db_index=True, max_length=255, unique=True)
