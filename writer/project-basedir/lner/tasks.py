import logging
import sys
import time
from datetime import datetime
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from rest_framework import serializers
from background_task import background

from common import lnclient
from common.log import logger
from common import validators
from common import json_util
from common import general_util

from posts.models import Post
from users.models import User
from lner.models import LightningNode
from lner.models import Invoice
from lner.models import InvoiceRequest

logger.info("Python version: {}".format(sys.version.replace("\n", " ")))


def human_time(ts):
    return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')


class CheckpointHelper(object):
    def __init__(self, node, invoice, creation_date):
        self.node = node
        self.invoice = invoice
        self.add_index = invoice.add_index
        self.creation_date = creation_date

        logger.info(
                (
                    "Processing invoice of node={} at add_index={} creation_date={}"
                ).format(
                    self.node.identity_pubkey,
                    self.add_index,
                    human_time(self.creation_date)
                )
        )

    def __repr__(self):
        return "node-{}-add-index-{}".format(self.node.pk, self.add_index)

    def set_checkpoint(self, checkpoint_value, action_type=None, action_id=None):
        if self.invoice.checkpoint_value == checkpoint_value:
            logger.info("Invoice already has this checkpoint {}".format(self))
        else:
            if action_type and action_id:
                self.invoice.performed_action_type = action_type
                self.invoice.performed_action_id = action_id

            self.invoice.checkpoint_value = checkpoint_value
            self.invoice.save()
            logger.info("Updated checkpoint to {}".format(self))

    def is_checkpointed(self):
        return self.invoice.checkpoint_value != "no_checkpoint"


@background(queue='queue-1', remove_existing_tasks=True)
def run():
    # Delete invoices that are passed retention
    for invoice_obj in Invoice.objects.all():
        if invoice_obj.created < timezone.now() - settings.INVOICE_RETENTION:
            logger.info("Deleting invoice {} because it is older then retention {}".format(invoice_obj, settings.INVOICE_RETENTION))
            invoice_request = InvoiceRequest.objects.get(id=invoice_obj.invoice_request.id)
            if invoice_request:
                invoice_request.delete()  # cascading delete also deletes the invoice
            else:
                logger.info("There was no invoice request, deleting just the invoice")
                invoice_obj.delete()
            continue

    node = LightningNode.objects.get()
    created = (node.global_checkpoint == -1)
    if created:
        logger.info("Global checkpoint does not exist")
        node.global_checkpoint = 0

    invoices_details = lnclient.listinvoices(
        index_offset=node.global_checkpoint,
        rpcserver=node.rpcserver,
        mock=settings.MOCK_LN_CLIENT
    )

    # example of invoices_details: {"invoices": [], 'first_index_offset': '5', 'last_index_offset': '72'}
    invoices_list = invoices_details['invoices']

    if settings.MOCK_LN_CLIENT:
        # Here the mock pulls invoices from DB Invoice model, while in prod invoices are pulled from the Lightning node
        # 1. Mocked lnclient.listinvoices returns an empty list
        # 2. The web front end adds the InvoiceRequest to the DB before it creates the actual invoices with lnclient.addinvoice
        # 3. Mocked API lnclient.addinvoice simply fakes converting InvoiceRequest to Invoice and saves to DB
        # 4. Here the mocked proces_tasks pulls invoices from DB Invoice model and pretends they came from lnclient.listinvoices
        # 5. After X seconds passed based on Invoice created time, here Mock update the Invoice checkpoint to "done" faking a payment 

        invoices_list = []
        for invoice_obj in Invoice.objects.all():
            invoice_request = InvoiceRequest.objects.get(id=invoice_obj.invoice_request.id)
            if invoice_request.lightning_node.id != node.id:
                continue

            mock_setteled = (invoice_obj.created + timedelta(seconds=3) < timezone.now())

            creation_unixtime = int(time.mktime(invoice_obj.created.timetuple()))
            invoices_list.append(
                {
                    "settled": mock_setteled,
                    "settle_date": str(int(time.time())) if mock_setteled else 0,
                    "state": "SETTLED" if mock_setteled else "OPEN",
                    "memo": invoice_request.memo,
                    "add_index": invoice_obj.add_index,
                    "payment_request": invoice_obj.pay_req,
                    "r_hash": invoice_obj.r_hash,
                    "creation_date": str(creation_unixtime),
                    "expiry": str(creation_unixtime + 120)
                }
            )

    logger.info("Got {} invoices".format(len(invoices_list)))

    retry_mini_map = {int(invoice['add_index']): False for invoice in invoices_list}

    for raw_invoice in invoices_list:
        # Example of raw_invoice:
        # {
        # 'htlcs': [], 
        # 'settled': False,
        # 'add_index': '5',
        # 'value': '1',
        # 'memo': '',
        # 'cltv_expiry': '40', 'description_hash': None, 'route_hints': [],
        # 'r_hash': '+fw...=', 'settle_date': '0', 'private': False, 'expiry': '3600',
        # 'creation_date': '1574459849',
        # 'amt_paid': '0', 'features': {}, 'state': 'OPEN', 'amt_paid_sat': '0',
        # 'value_msat': '1000', 'settle_index': '0',
        # 'amt_paid_msat': '0', 'r_preimage': 'd...=', 'fallback_addr': '',
        # 'payment_request': 'lnbc...'
        # }
        created = general_util.unixtime_to_datetime(int(raw_invoice["creation_date"]))
        if created < general_util.now() - settings.INVOICE_RETENTION:
            logger.info("Got old invoice from listinvoices, skipping... {} is older then retention {}".format(
                created,
                settings.INVOICE_RETENTION
                )
            )
            continue

        try:
            invoice = Invoice.objects.get(add_index=int(raw_invoice["add_index"]))
        except Invoice.DoesNotExist:
            logger.error("Unknown add_index. Skipping invoice...")
            logger.error("Raw invoice was: {}".format(raw_invoice))
            continue

        # Validate
        assert invoice.invoice_request.memo == raw_invoice["memo"]
        assert invoice.pay_req == raw_invoice["payment_request"]

        checkpoint_helper = CheckpointHelper(
            node=node,
            invoice=invoice,
            creation_date=raw_invoice["creation_date"]
        )

        if checkpoint_helper.is_checkpointed():
            continue

        if raw_invoice['state'] == 'CANCELED':
            checkpoint_helper.set_checkpoint("canceled")
            continue

        if raw_invoice['settled'] and (raw_invoice['state'] != 'SETTLED' or int(raw_invoice['settle_date']) == 0):
            checkpoint_helper.set_checkpoint("inconsistent")
            continue

        if time.time() > int(raw_invoice['creation_date']) + int(raw_invoice['expiry']):
            checkpoint_helper.set_checkpoint("expired")
            continue

        if not raw_invoice['settled']:
            logger.info("Skipping invoice at {}: Not yet settled".format(checkpoint_helper))
            retry_mini_map[checkpoint_helper.add_index] = True
            continue  # try again later

        #
        # Invoice is settled
        #

        logger.info("Processing invoice at {}: SETTLED".format(checkpoint_helper))

        memo = raw_invoice["memo"]
        try:
            post_details = json_util.deserialize_memo(memo)
        except json_util.JsonUtilException:
            checkpoint_helper.set_checkpoint("deserialize_failure")
            continue

        try:
            validators.validate_memo(post_details)
        except ValidationError as e:
            logger.exception(e)
            checkpoint_helper.set_checkpoint("memo_invalid")
            continue

        logger.info("Post details {}".format(post_details))
        user, created = User.objects.get_or_create(pubkey='Unknown')
        post = Post(
            author=user,
            parent=None,
            type=post_details["post_type"],
            title=post_details["title"],
            content=post_details["content"],
            tag_val=post_details["tag_val"],
        )
        post.save()

        checkpoint_helper.set_checkpoint("done", action_type="post", action_id=post.id)

    # advance global checkpoint
    new_global_checkpoint = None
    for add_index in sorted(retry_mini_map.keys()):
        retry = retry_mini_map[add_index]
        if retry:
            break
        else:
            logger.info("add_index={} advances global checkpoint".format(add_index))
            new_global_checkpoint = add_index

    if new_global_checkpoint:
        node.global_checkpoint = new_global_checkpoint
        node.save()
        logger.info("Saved new global checkpoint {}".format(new_global_checkpoint))

# schedule a new task after "repeat" number of seconds
run(repeat=1)
