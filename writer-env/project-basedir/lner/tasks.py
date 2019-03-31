import logging

from background_task import background

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

@background(queue='queue-1', remove_existing_tasks=True)
def hello():
    logger.info("Hello World!")

hello(repeat=5)