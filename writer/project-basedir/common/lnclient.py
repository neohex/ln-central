from common import util

LNCLI_BIN = "/home/lightning/gocode/bin/lncli"
AUTH_ARGS = [
    "--macaroonpath", "/etc/biostar/invoice.macaroon",
    "--tlscertpath", "/etc/biostar/tls.cert",
    "--rpcserver", "ec2-34-217-175-162.us-west-2.compute.amazonaws.com:10009"
]

def addinvoice(memo):
    cmd = [LNCLI_BIN] + AUTH_ARGS + ["addinvoice", "--memo", memo, "--amt", "300"]
    return util.run(cmd)

def listinvoices(index_offset):
    cmd =  [LNCLI_BIN] + AUTH_ARGS + ["listinvoices", "--index_offset", str(index_offset), "--reversed=false"]
    return util.run(cmd)