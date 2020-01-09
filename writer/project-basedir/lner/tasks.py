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
from lner.models import InvoiceListCheckpoint

logger.info("Python version: {}".format(sys.version.replace("\n", " ")))


def human_time(ts):
    return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')


class CheckpointHelper(object):
    def __init__(self, node, add_index, creation_date):
        self.node = node
        self.add_index = int(add_index)
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
        return self._gen_checkpoint_name()

    def _gen_checkpoint_name(self):
        return "node-{}-add-index-{}".format(self.node.pk, self.add_index)

    def set_checkpoint(self, comment):
        checkpoint_name = self._gen_checkpoint_name()
        validators.validate_checkpoint_name(checkpoint_name)  # TODO: make it run automatically in models and serializers

        logger.info("Checkpointing invoice, checkpoint_name={} comment={}".format(checkpoint_name, comment))

        try:
            checkpoint = InvoiceListCheckpoint.objects.get(
                lightning_node=self.node,
                checkpoint_name=checkpoint_name
            )
        except InvoiceListCheckpoint.DoesNotExist:
            checkpoint = InvoiceListCheckpoint(
                lightning_node=self.node,
                checkpoint_name=checkpoint_name
            )
            checkpoint.checkpoint_value = 1
            checkpoint.comment = comment
            checkpoint.save()
            logger.info("Created new checkpoint {}".format(checkpoint_name))
        else:
            checkpoint.checkpoint_value = 1
            checkpoint.comment = comment
            checkpoint.save()
            logger.info("Overwrote existing checkpoint {}".format(checkpoint_name))


    def get_checkpoint(self):
        checkpoint_name = self._gen_checkpoint_name()
        try:
            checkpoint = InvoiceListCheckpoint.objects.get(
                lightning_node=self.node,
                checkpoint_name=checkpoint_name
            )
        except InvoiceListCheckpoint.DoesNotExist:
            return False

        return checkpoint.checkpoint_value > 0


@background(queue='queue-1', remove_existing_tasks=True)
def run():
    logger.info("\nprocess_tasks-----------------")
    node = LightningNode.objects.get()

    global_checkpoint, created = InvoiceListCheckpoint.objects.get_or_create(
        lightning_node=node,
        checkpoint_name="global-offset",
    )

    if created:
        logger.info("New global checkpoint created: global-offset")

    invoices_details = lnclient.listinvoices(
        index_offset=global_checkpoint.checkpoint_value,
        rpcserver=node.rpcserver,
        mock=settings.MOCK_LN_CLIENT
    )

    # example of invoices_details: {"invoices": [], 'first_index_offset': '5', 'last_index_offset': '72'}
    invoices_list = invoices_details['invoices']
    logger.info("Got {} invoices".format(len(invoices_list)))

    retry_mini_map = {int(invoice['add_index']):False for invoice in invoices_list}

    for invoice in invoices_list:
        # Example of invoice:
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
        # 'amt_paid_msat': '0', 'r_preimage': 'd...=', 'fallback_addr': '', 'payment_request': 'lnbc...'
        # }

        checkpoint_helper = CheckpointHelper(node, int(invoice["add_index"]), invoice["creation_date"])

        if checkpoint_helper.get_checkpoint():
            continue

        if invoice['state'] == 'CANCELED':
            comment = "canceled"
            checkpoint_helper.set_checkpoint(comment=comment)
            continue

        if invoice['settled'] and (invoice['state'] != 'SETTLED' or int(invoice['settle_date']) == 0):
            comment = "inconsistent"
            checkpoint_helper.set_checkpoint(comment=comment)
            continue

        if time.time() > int(invoice['creation_date']) + int(invoice['expiry']):
            comment = "expired"
            checkpoint_helper.set_checkpoint(comment=comment)
            continue

        if not invoice['settled']:
            logger.info("Skipping invoice at {}: Not yet settled".format(checkpoint_helper))
            retry_mini_map[checkpoint_helper.add_index] = True
            continue  # try again later

        #
        # Invoice is settled
        #

        logger.info("Processing invoice at {}: SETTLED".format(checkpoint_helper))

        memo = invoice["memo"]
        try:
            post_details = json_util.deserialize_memo(memo)
        except json_util.JsonUtilException:
            comment="deserialize_failure"
            checkpoint_helper.set_checkpoint(comment=comment)
            continue

        try:
            validators.validate_memo(post_details)
        except ValidationError as e:
            comment = "memo_invalid"
            logger.exception(e)
            checkpoint_helper.set_checkpoint(comment=comment)
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

        checkpoint_helper.set_checkpoint(comment="done")

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
        global_checkpoint.checkpoint_value = new_global_checkpoint
        global_checkpoint.save()
        logger.info("Saved new global checkpoint {}".format(new_global_checkpoint))

run(repeat=1)
