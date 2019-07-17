import logging
import requests

from django.conf import settings


logger = logging.getLogger(__name__)

class LNUtilError(Exception):
    pass
        
def call_endpoint(path, args=""):
    if settings.READER_TO_WRITER_AUTH_TOKEN is not None:
        headers = {'Authorization': 'Token {}'.format(settings.READER_TO_WRITER_AUTH_TOKEN)}
    else:
        headers = {}

    full_path = 'http://127.0.0.1:8000/{}.json?{}'.format(path, args)
    try:
        return requests.get(full_path)

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
    except TypeError:
        error_msg = "Got invalid response from API server: {} status_code={} response_text={}".format(
            response.reason, response.status_code, response.text
        )

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


def add_invoice(memo):
    response = call_endpoint('ln/addinvoice', args="memo={}".format(memo))

    check_expected_key(response, "pay_req")
        
    return response.json()
