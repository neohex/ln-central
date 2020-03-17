"""
Setting common to reader and writer
"""

from datetime import timedelta

PAYMENT_AMOUNT = 2  # in satoshi

MAX_MEMO_SIZE = 600  # includes the length of the friendly prefix
MAX_PAYREQ_SIZE = 2000  # pay_req includes memo and routing info
FRIENDLY_PREFIX = "ln.support"  # cannot have under-bars (_s)

INVOICE_EXPIRY = 3600  # in seconds
INVOICE_RETENTION = timedelta(weeks=1)  # how long to keep invoice requests and invoices
