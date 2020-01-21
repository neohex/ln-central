import logging
import sys
import time
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError

from rest_framework import serializers
from background_task import background

from common import lnclient
from common.log import logger
from common import validators
from common import json_util
from posts.models import Post
from users.models import User
from lner.models import LightningNode
from lner.models import Invoice

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
        invoices_list += [
            {
                'settled': False,
                'add_index': node.global_checkpoint + 1
            }
        ]

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
