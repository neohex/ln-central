import logging

from django.conf import settings
from background_task import background
from common import util
from common import lnclient


logger = util.getLogger("lner.tasks")


@background(queue='queue-1', remove_existing_tasks=True)
def run():
    invoices = lnclient.listinvoices(index_offset=4, mock=settings.MOCK_LN_CLIENT)
    logger.info("Got {} invoices".format(len(invoices)))

run(repeat=1)