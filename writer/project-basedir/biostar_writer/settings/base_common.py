"""
Setting common to reader and writer
"""

PAYMENT_AMOUNT = 2  # in satoshi

MAX_MEMO_SIZE = 1000  # includes the length of the friendly prefix
MAX_PAYREQ_SIZE = 2000  # pay_req includes memo and routing info
FRIENDLY_PREFIX = "ln.support"  # cannot have under-bars (_s)

INVOICE_EXPIRY = 3600  # in seconds
