from django.db import models
from common import validators
from django.conf import settings
from django.utils import timezone

class LightningNode(models.Model):
    identity_pubkey = models.CharField(verbose_name='LN Identity Pubkey', db_index=True, max_length=255, unique=True)
    rpcserver = models.CharField(verbose_name='host:port of ln daemon', max_length=255, default="localhost:10009")
    global_checkpoint = models.IntegerField(
        verbose_name='add_index of the last global checkpoint',
        default=-1
    )
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(LightningNode, self).save(*args, **kwargs)

class InvoiceRequest(models.Model):
    lightning_node = models.ForeignKey(LightningNode, on_delete=models.CASCADE)
    memo = models.CharField(
        verbose_name='LN Invoice memo',
        unique=True,
        max_length=settings.MAX_MEMO_SIZE
    )
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(InvoiceRequest, self).save(*args, **kwargs)

class Invoice(models.Model):
    invoice_request = models.ForeignKey(InvoiceRequest, null=True, default=None, on_delete=models.CASCADE)
    r_hash = models.CharField(verbose_name='LN Invoice r_hash', max_length=255, default="__DEFAULT__")
    pay_req = models.CharField(verbose_name='LN Invoice pay_req', max_length=settings.MAX_PAYREQ_SIZE)
    add_index = models.IntegerField(verbose_name='LN Invoice add_index', default=-1)
    checkpoint_value =  models.CharField(
        verbose_name='E.g. done, expired, canceled, deserialize_failure, or memo_invalid.',
        max_length=255,
        default="no_checkpoint"
    )
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Invoice, self).save(*args, **kwargs)
