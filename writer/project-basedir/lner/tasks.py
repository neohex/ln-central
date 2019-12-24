import logging
import sys
import time
from datetime import datetime

from django.conf import settings
from background_task import background
from common import lnclient
from common.log import logger

from lner.models import LightningNode
from lner.models import InvoiceListCheckpoint
from common import json_util
from posts.models import Post
from users.models import User

logger.info("Python version: {}".format(sys.version.replace("\n", " ")))


def human_time(ts):
    return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')

def _set_checkpoint(node, add_index, comment):
    checkpoint, created = InvoiceListCheckpoint.objects.get_or_create(
        lightning_node=node,
        checkpoint_name="offset_{}".format(add_index),
    )

    if not created:
        logger.info("Overwrting existing checkpoint add_index={}".format(add_index))

    checkpoint.checkpoint_value = 1
    checkpoint.comment = comment
    checkpoint.save()

def _get_checkpoint(node, add_index):
    try:
        checkpoint = InvoiceListCheckpoint.objects.get(
            lightning_node=node,
            checkpoint_name="offset_{}".format(add_index),
        )
    except InvoiceListCheckpoint.DoesNotExist:
        return False

    return checkpoint.checkpoint_value > 0


@background(queue='queue-1', remove_existing_tasks=True)
def run():
    node = LightningNode.objects.get()

    checkpoint, created = InvoiceListCheckpoint.objects.get_or_create(
        lightning_node=node,
        checkpoint_name="global_offset",
    )

    if created:
        logger.info("New global checkpoint created")

    invoices_details = lnclient.listinvoices(
        index_offset=checkpoint.checkpoint_value,
        rpcserver=node.rpcserver,
        mock=settings.MOCK_LN_CLIENT
    )

    # example of invoices_details: {"invoices": [], 'first_index_offset': '5', 'last_index_offset': '72'}
    invoices_list = invoices_details['invoices']
    logger.info("Got {} invoices".format(len(invoices_list)))

    for invoice in invoices_list:
        # example of invoice:
        # {'htlcs': [], 'settled': False, 'add_index': '5', 'cltv_expiry': '40', 'description_hash': None, 'route_hints': [],
        # 'r_hash': '+fw...=', 'settle_date': '0', 'private': False, 'expiry': '3600', 'creation_date': '1574459849', 'value': '1',
        # 'amt_paid': '0', 'features': {}, 'state': 'OPEN', 'amt_paid_sat': '0', 'memo': '', 'value_msat': '1000', 'settle_index': '0',
        # 'amt_paid_msat': '0', 'r_preimage': 'd...=', 'fallback_addr': '', 'payment_request': 'lnbc...'}

        add_index = int(invoice['add_index'])

        if _get_checkpoint(node=node, add_index=add_index):
            continue

        logger.info(
                (
                    "Processing invoice add_index={} creation_date={}"
                ).format(
                    add_index,
                    human_time(invoice['creation_date'])
                )
        )

        if invoice['state'] == 'CANCELED':
            comment = "canceled"
            logger.info("Checkpointing invoice at index {}: {}".format(add_index, comment))
            _set_checkpoint(node=node, add_index=add_index, comment=comment)
            continue

        if invoice['settled'] and (invoice['state'] != 'SETTLED' or int(invoice['settle_date']) == 0):
            comment = "inconsistent"
            logger.info("Checkpointing invoice at index {}: {}".format(add_index, comment))
            _set_checkpoint(node=node, add_index=add_index, comment=comment)
            continue

        if time.time() > int(invoice['creation_date']) + int(invoice['expiry']):
            comment = "expired"
            logger.info("Checkpointing invoice at index {}: {}".format(add_index, comment))
            _set_checkpoint(node=node, add_index=add_index, comment=comment)
            continue

        if not invoice['settled']:
            logger.info("Skipping invoice at index {}: Not yet settled".format(invoice['add_index']))
            continue  # try again later

        #
        # Invoice is settled
        #

        logger.info("Processing invoice at index {}: SETTLED".format(invoice['add_index']))

        memo = invoice["memo"]
        logger.info("Memo: {}".format(memo))

        try:
            post_details = json_util.deserialize_memo(memo)
        except json_util.JsonUtilException:
            comment="deserialize_failure"
            logger.info("Checkpointing invoice at index {}: {}".format(add_index, comment))
            _set_checkpoint(node=node, add_index=add_index, comment=comment)
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


run(repeat=1)
