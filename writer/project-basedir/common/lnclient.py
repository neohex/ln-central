from common import cli

import json
import time
import random

LNCLI_BIN = "/home/lightning/gocode/bin/lncli"
AUTH_ARGS = [
    "--macaroonpath", "/etc/biostar/writer-{rpcserver}-invoice.macaroon",
    "--tlscertpath", "/etc/biostar/writer-{rpcserver}-tls.cert",
    "--rpcserver", "{rpcserver}"
]


def _sanitize_rpcserver(rpcserver):
    parts = rpcserver.split(":")
    assert len(parts) <= 2, "too many :s in rpcserver"
    assert parts[0].isalnum(), "rpcserver host part in not alphanumeric"
    if len(parts) == 2:
        assert parts[1].isdigit(), "rpcserver port part is not a number"


def _auth_args(rpcserver):
    _sanitize_rpcserver(rpcserver)
    return [arg.format(rpcserver=rpcserver) for arg in AUTH_ARGS]


def addinvoice(memo, rpcserver, amt, expiry):
    """
    TODO (2019-??-??): check for [lncli] rpc error: code = Unknown desc = memo too large: 1192 bytes (maxsize=1024)
    """
    cmd = [LNCLI_BIN] + _auth_args(rpcserver) + ["addinvoice", "--memo", memo, "--amt", str(amt), "--expiry", str(expiry)]
    output = cli.run(cmd)
    print("Command finished, addinvoice json stdout: {}".format(output))
    return output


def listinvoices(index_offset, rpcserver, max_invoices=100, mock=False):
    if mock:
        return {
            "first_index_offset": "0",
                "invoices": [],
                "last_index_offset": "0"
            }

    cmd =  [LNCLI_BIN] + _auth_args(rpcserver) + [
        "listinvoices",
        "--index_offset", str(index_offset),
        "--max_invoices", str(max_invoices),
        "--reversed=False"
    ]

    return cli.run(cmd, log_cmd=False)

def verifymessage(msg, sig, mock=False):
    if mock:
        return {
            "valid": True,
            "pubkey": "FAKE2"
        }

    cmd =  [LNCLI_BIN] + _auth_args(rpcserver) + [
        "verifymessage",
        "--msg", msg,
        "--sig", sig
    ]

    return cli.run(cmd, log_cmd=False)
