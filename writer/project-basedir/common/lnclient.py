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


def addinvoice(memo, rpcserver, amt, mock=False):
    """
    TODO: check for [lncli] rpc error: code = Unknown desc = memo too large: 1192 bytes (maxsize=1024)
    """
    if mock:
        return {
                "pay_req": str(int(random.random() * (10 ** 15))),
             }

    cmd = [LNCLI_BIN] + _auth_args(rpcserver) + ["addinvoice", "--memo", memo, "--amt", str(amt)]
    output = cli.run(cmd)
    print("Command finished, addinvoice json stdout: {}".format(output))
    return output


def listinvoices(index_offset, rpcserver, max_invoices=100, mock=False):
    if mock:
        return {
            "first_index_offset": "5",
                "invoices": [
                    # canceled
                    {
                        "add_index": "5",
                        "amt_paid": "0",
                        "amt_paid_msat": "0",
                        "amt_paid_sat": "0",
                        "cltv_expiry": "144",
                        "creation_date": "1553539556",
                        "description_hash": None,
                        "expiry": "3600",
                        "fallback_addr": "",
                        "memo": "",
                        "payment_request": "lnbc10n1pwfjg0ypp5v2ksf0y5jktv99dejrlvvaueycsy5t5wv6edkcac6lhw570pk3xqdqqcqzysvhp2h3lplqzveeeyd5wrcama6en7uvpesf6tzw22jjjvewvqx8nxm4w0lfp408gwp2kpde0zcc54dyzy6qfydmqfj8enqrgeck7nd0qpc3glz8",
                        "private": False,
                        "r_hash": "Yq0EvJSVlsKVuZD+xneZJiBKLo5msttjuNfu6nnhtEw=",
                        "r_preimage": "iNVsIebZuYKZfc+AAnJXTYDGccOpYp90zBHp4i8XPss=",
                        "receipt": None,
                        "route_hints": [],
                        "settle_date": "0",
                        "settle_index": "0",
                        "settled": False,
                        "state": "CANCELED",
                        "value": "1"
                    },
                    # inconsistent
                    {
                        "add_index": "6",
                        "amt_paid": "0",
                        "amt_paid_msat": "0",
                        "amt_paid_sat": "0",
                        "cltv_expiry": "144",
                        "creation_date": "1553539556",
                        "description_hash": None,
                        "expiry": "3600",
                        "fallback_addr": "",
                        "memo": "",
                        "payment_request": "lnbc10n1pwfjg0ypp5yr420mc49lr0vglgv7f828s722u566eeafw0qx35nhzv9907yngsdqqcqzysmdlnq09y84durc6wm84ktzfe79uvtw6mfkuxre0hwemkzfvlcd75etjx8n3heldpldrla6d0v5lmrzm6ndy4javzppka0fzwugzdkngpg8t45v",
                        "private": False,
                        "r_hash": "IOqn7xUvxvYj6GeSdR4eUrlNaznqXPAaNJ3EwpX+JNE=",
                        "r_preimage": "HI0r47w/8XI2DL7wZv3x+1wv16gAZ+MQ9kEYW2je/XE=",
                        "receipt": None,
                        "route_hints": [],
                        "settle_date": "0",
                        "settle_index": "0",
                        "settled": True,
                        "state": "OPEN",
                        "value": "1"
                    },
                    # expired
                    {
                        "add_index": "7",
                        "amt_paid": "1000",
                        "amt_paid_msat": "1000",
                        "amt_paid_sat": "1",
                        "cltv_expiry": "144",
                        "creation_date": "1553548298",
                        "description_hash": None,
                        "expiry": "3600",
                        "fallback_addr": "",
                        "memo": "",
                        "payment_request": "lnbc10n1pwfj3q2pp5gr94th7ug7zlqfu6cugkf6z6hv30dnyqg3z2fsgeuz6e575sfqjqdqqcqzysajw5pv9pu9jlp0t8zvyqc63hweeyzztxnlvjfrgvuwt0dl4nrd4xh78t25jyp6psryr8xx5s5skyafltsp90dn4chgg7fwq0rmq92gcqvlhems",
                        "private": False,
                        "r_hash": "QMtV39xHhfAnmscRZOhauyL2zIBERKTBGeC1mnqQSCQ=",
                        "r_preimage": "+iTb5Sx5aqWMGCeUmRe4OVUcu0cyYmieIZi2jcGpXQw=",
                        "receipt": None,
                        "route_hints": [],
                        "settle_date": "1553548314",
                        "settle_index": "4",
                        "settled": True,
                        "state": "SETTLED",
                        "value": "1"
                    },
                    # open
                    {
                        "add_index": "8",
                        "amt_paid": "1000",
                        "amt_paid_msat": "1000",
                        "amt_paid_sat": "1",
                        "cltv_expiry": "144",
                        "creation_date": str(int(time.time())),  # so it's not expired
                        "description_hash": None,
                        "expiry": "3600",
                        "fallback_addr": "",
                        "memo": "",
                        "payment_request": "lnbc10n1pwfj3q2pp5jzhn5f79lzlpns63rvj58k5ykxd2nn838lm9vxsnunwxr786wmdqdqqcqzysgnrakfhzrhfntwu48t0x6xhft5dwxqvyx2cjgvc8g5dz686c9c2jllclzq9duej5nzajdc5u4gtmchjnnvgfzyf0km4m756zunr2shgq496zkl",
                        "private": False,
                        "r_hash": "kK86J8X4vhnDURslQ9qEsZqpzPE/9lYaE+TcYfj6dto=",
                        "r_preimage": "yUSyH1Smmba2+MIgWd8UAtksKsgyKNokioeTUl9BUvA=",
                        "receipt": None,
                        "route_hints": [],
                        "settle_date": "0",
                        "settle_index": "5",
                        "settled": False,
                        "state": "OPEN",
                        "value": "1"
                    },
                    # settled
                    {
                        "add_index": "9",
                        "amt_paid": "1000",
                        "amt_paid_msat": "1000",
                        "amt_paid_sat": "1",
                        "cltv_expiry": "144",
                        "creation_date": str(int(time.time())),  # so it's not expired
                        "description_hash": None,
                        "expiry": "3600",
                        "fallback_addr": "",
                        "memo": "",
                        "payment_request": "lnbc10n1pwfj3q2pp5ud0fz0yzshvlwnt05le5ttnhzhk84vuwdxaydj0mdey7jwzc9p6sdqqcqzysz7jlefs9der6qwr859cz54dxscsh2kqe88jag2gw90r8xd6wkj3hh85mvrjtsvj2h9gxyqs5jnmzemwqgau0wy6wvde7aqjna8ra5mqpchv394",
                        "private": False,
                        "r_hash": "416RPIKF2fdNb6fzRa53Fex6s45pukbJ+25J6ThYKHU=",
                        "r_preimage": "Gb0RYCFe1vtA1PJP4dOi+G0aIZOmby/9bRoFdCB7L6M=",
                        "receipt": None,
                        "route_hints": [],
                        "settle_date": "1553548394",
                        "settle_index": "6",
                        "settled": True,
                        "state": "SETTLED",
                        "value": "1"
                    }
                ],
                "last_index_offset": "32"
            }

    cmd =  [LNCLI_BIN] + _auth_args(rpcserver) + [
        "listinvoices", 
        "--index_offset", str(index_offset),
        "--max_invoices", str(max_invoices), 
        "--reversed=False"
    ]
    
    return cli.run(cmd)
