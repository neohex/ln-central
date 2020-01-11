from django.db import models
from common import validators
from django.conf import settings

class LightningNode(models.Model):
    identity_pubkey = models.CharField(verbose_name='LN Identity Pubkey', db_index=True, max_length=255, unique=True)
    rpcserver = models.CharField(verbose_name='host:port of ln daemon', max_length=255, default="localhost:10009")

class LightningInvoiceRequest(models.Model):
    lightning_node = models.ForeignKey(LightningNode, on_delete=models.CASCADE)
    memo = models.CharField(verbose_name='LN Invoice memo', unique=True, max_length=settings.MAX_MEMO_SIZE)
    comment = models.CharField(
        verbose_name='A copy of comment from InvoiceListCheckpoint for scalability',
        max_length=255,
        default="__DEFAULT__"
    )

class LightningInvoice(models.Model):
    lightning_invoice_request = models.ForeignKey(LightningInvoiceRequest, null=True, default=None, on_delete=models.CASCADE)
    r_hash = models.CharField(verbose_name='LN Invoice r_hash', max_length=255, default="__DEFAULT__")
    pay_req = models.CharField(verbose_name='LN Invoice pay_req', max_length=settings.MAX_MEMO_SIZE)
    add_index = models.IntegerField(verbose_name='LN Invoice add_index', default=-1)

class InvoiceListCheckpoint(models.Model):
    lightning_node = models.ForeignKey(LightningNode, on_delete=models.CASCADE)
    checkpoint_name = models.CharField(
        verbose_name='Checkpoint name. Encodes relationships with data such as node pubkey and add_index. This relationship is not in the database for scalability and flexibility.',
        max_length=255,
        default="__DEFAULT__",
        unique=True,
        validators=[validators.validate_checkpoint_name]
    )
    checkpoint_value = models.IntegerField(verbose_name='Integer value of the checkpoint (e.g. offset). Zero invalidates checkpoint.', default=1)
    comment = models.CharField(
        verbose_name='Comment. Explanation of reason for checkpoint. E.g. "done", "canceled", "deserialize_failure", or "memo_invalid".',
        max_length=255,
        default="__DEFAULT__"
    )