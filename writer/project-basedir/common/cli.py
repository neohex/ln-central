import time

import datetime
import json
import subprocess

from common.log import logger


class RunCommandException(Exception):
    pass


def h(cmd):
	"""
	Human readable cmd
	"""
	results = []
	results += [cmd[0] + " \\"]
	results += ["  {} \\".format(c) for c in cmd[1:-1]]
	results += ["  {}".format(cmd[-1])]

	return "\n".join(results)

def run(cmd, timeout=5, try_num=3, run_try_sleep=1, log_cmd=True):
    if log_cmd:
        logger.info("Running command: {}".format(h(cmd)))

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
            raise RunCommandException("Run command {} timeout after {} seconds".format(h(cmd), accumulated_timeout))

    else:
        raise RunCommandException("Failed command: {}".format(h(cmd)))

    return json.loads(raw)
