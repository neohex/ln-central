import logging

def getLogger(name):
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname).1s [%(filename)s:%(lineno)d] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


logger = getLogger(__name__)
