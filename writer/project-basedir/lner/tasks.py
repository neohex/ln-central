import logging

from django.conf import settings
from background_task import background
from common import lnclient
from common.log import logger
from lner.models import LightningNode

@background(queue='queue-1', remove_existing_tasks=True)
def run():
    node = LightningNode.objects.get()
    invoices = lnclient.listinvoices(index_offset=4, rpcserver=node.rpcserver, mock=settings.MOCK_LN_CLIENT)

    # example invoices: {"invoices": [], 'first_index_offset': '5', 'last_index_offset': '72'}
    logger.info("Got {} invoices".format(len(invoices['invoices'])))

run(repeat=1)
