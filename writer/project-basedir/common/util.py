import logging
import time

import datetime
import json
import subprocess


def getLogger(name):
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


logger = getLogger(__name__)


class RunCommandException(Exception):
    pass


def run(cmd, timeout=5, try_num=3, run_try_sleep=1):
    logger.info("Running command: {}".format(cmd))
    accumulated_timeout = 0
    for _ in range(try_num):
        try_start = time.time()
        try:
            raw = subprocess.check_output(
                   cmd,
                   timeout=timeout
                ).decode("utf-8")
            break
        except Exception as e:
            print(e)
            print("Sleeping for {} seconds".format(run_try_sleep))
            time.sleep(run_try_sleep)

        try_duration = time.time() - try_start
        accumulated_timeout += try_duration

        if accumulated_timeout > timeout:
            raise RunCommandException("Run command {} timeout after {} seconds".format(cmd, accumulated_timeout))

    else:
        raise RunCommandException("Failed command: {}".format(cmd))

    return json.loads(raw)
