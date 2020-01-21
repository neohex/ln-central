import logging
import requests

from django.conf import settings


CHECKPOINT_DONE = 1
CHECKPOINT_WAIT = 2
CHECKPOINT_ERROR = 3

logger = logging.getLogger(__name__)

class LNUtilError(Exception):
    pass
        
def call_endpoint(path, args={}, as_post=False):
    if settings.READER_TO_WRITER_AUTH_TOKEN is not None:
        headers = {'Authorization': 'Token {}'.format(settings.READER_TO_WRITER_AUTH_TOKEN)}
    else:
        headers = {}

    full_path = 'http://127.0.0.1:8000/{}.json'.format(path)
    try:
        if as_post:
            return requests.post(full_path, headers=headers, data=args)
        else:
            return requests.get(full_path, headers=headers, params=args)

    except requests.exceptions.ConnectionError as e:
        logger.exception(e)
        raise LNUtilError("ConnectionError when connecting to {}".format(full_path))


def check_expected_key(response, expected_key, is_list=True):
    try:
        if is_list:
            [n[expected_key] for n in response.json()]
        else:
            response.json()[expected_key]

    except ValueError:
        error_msg = "Got non-json from API server: {} status_code={}".format(
            response.reason, response.status_code
        )
      
        logger.error(error_msg)
        raise LNUtilError(error_msg)

    except KeyError:
        error_msg = "Got invalid schema from API server: {} status_code={} response_text={}".format(
            response.reason, response.status_code, response.text
        )

        logger.error(error_msg)
        raise LNUtilError(error_msg)
    except TypeError as e:
        error_msg = (
            (
                "Is is_list correct for check_expected_key? "
                "Got TypeError for a valid response from API "
                "server: {} status_code={} response_text={} exception={}"
            ).format(
                    response.reason, response.status_code, response.text, e
            )
        )

        logger.exception(e)
        logger.error(error_msg)
        raise LNUtilError(error_msg)


def get_nodes_list():   
    try:
        response = call_endpoint('ln/list')
        check_expected_key(response, "identity_pubkey")

    except LNUtilError:
        return []

    else:
        return [n["identity_pubkey"] for n in response.json()]


def add_invoice(memo, node_id=1):
    response = call_endpoint('ln/addinvoice', args={"memo": memo, "node_id": node_id}, as_post=True)

    check_expected_key(response, "pay_req", is_list=False)
        
    return response.json()

def check(memo, node_id=1):
    response = call_endpoint('ln/check', args={"memo": memo, "node_id": node_id})
    if response.status_code == 404:
        return CHECKPOINT_WAIT

    if response.status_code != 200:
        logger.error(
            "Got API error when looking up checkpoint, http_status={},node={},memo={}".format(
                response.status_code,
                node_id,
                memo
            )
        )
        return CHECKPOINT_ERROR

    check_expected_key(response, "checkpoint_value", is_list=True)

    response_parsed = response.json()[0]
    checkpoint_value = response_parsed["checkpoint_value"]

    if checkpoint_value == "done":
        return CHECKPOINT_DONE
    elif checkpoint_value == "no_checkpoint":
        return CHECKPOINT_WAIT
    else:
        logger.error(
            "Got checkpoint error: {} for node={},memo={}".format(
                checkpoint_value,
                node_id,
                memo
            )
        )
        return CHECKPOINT_ERROR
