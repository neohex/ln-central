from django.db import models

class LightningNode(models.Model):
    identity_pubkey = models.CharField(verbose_name='LN Identity Pubkey', db_index=True, max_length=255, unique=True)
    rpcserver = models.CharField(verbose_name='host:port of ln daemon', max_length=255, default="localhost:10009")

class LightningInvoice(models.Model):
    r_hash = models.CharField(verbose_name='LN Invoice r_hash', max_length=255, default="__DEFAULT__")
    pay_req = models.CharField(verbose_name='LN Invoice pay_req', max_length=255)
    add_index = models.IntegerField(verbose_name='LN Invoice add_index', default=-1)

class InvoiceListCheckpoint(models.Model):
    lightning_node = models.ForeignKey(LightningNode, on_delete=models.CASCADE)
    checkpoint_name = models.CharField(verbose_name='Checkpoint name', max_length=255, default="__DEFAULT__")
    add_index = models.IntegerField(verbose_name='LN Invoice add_index', default=0)
