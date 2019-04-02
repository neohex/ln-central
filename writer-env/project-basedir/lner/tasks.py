import logging

from background_task import background
from common import util

logger = util.logger()

@background(queue='queue-1', remove_existing_tasks=True)
def hello():
    logger.info("Hello World!")

hello(repeat=5)