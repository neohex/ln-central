import logging
import sys
from datetime import datetime

from django.conf import settings
from background_task import background
from common import lnclient
from common.log import logger

from lner.models import LightningNode
from common import json_util
from posts.models import Post
from users.models import User

def human_time(ts):
    return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')

@background(queue='queue-1', remove_existing_tasks=True)
def run():
    logger.info("Python version: {}".format(sys.version))

    node = LightningNode.objects.get()
    invoices_details = lnclient.listinvoices(index_offset=70, rpcserver=node.rpcserver, mock=settings.MOCK_LN_CLIENT)

    # example of invoices_details: {"invoices": [], 'first_index_offset': '5', 'last_index_offset': '72'}
    invoices_list = invoices_details['invoices']
    logger.info("Got {} invoices".format(len(invoices_list)))

    for invoice in invoices_list:
        # example of invoice:
        # {'htlcs': [], 'settled': False, 'add_index': '5', 'cltv_expiry': '40', 'description_hash': None, 'route_hints': [],
        # 'r_hash': '+fw...=', 'settle_date': '0', 'private': False, 'expiry': '3600', 'creation_date': '1574459849', 'value': '1',
        # 'amt_paid': '0', 'features': {}, 'state': 'OPEN', 'amt_paid_sat': '0', 'memo': '', 'value_msat': '1000', 'settle_index': '0',
        # 'amt_paid_msat': '0', 'r_preimage': 'd...=', 'fallback_addr': '', 'payment_request': 'lnbc...'}
        logger.info(
                "Processing invoice that was created on %s",
                human_time(invoice['creation_date'])
        )
        if invoice['settled']:
            logger.info("Processing invoice {}".format(invoice))

            memo = invoice["memo"]
            logger.info("Memo {}".format(memo))

            post_details = json_util.deserialize_memo(memo)
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
