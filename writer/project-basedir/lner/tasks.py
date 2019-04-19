import logging

from background_task import background
from common import util
from common import lnclient


logger = util.getLogger("lner.tasks")


@background(queue='queue-1', remove_existing_tasks=True)
def hello():
    logger.info("Hello World! {}".format(lnclient.listinvoices(index_offset=4)))

hello(repeat=1)