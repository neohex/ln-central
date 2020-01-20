# Create your views here.
import os
import io
import time

from django import forms
from django.views.generic import  UpdateView, DetailView, TemplateView
from django.http import HttpResponseRedirect
from django.http import Http404
from django.conf import settings

from biostar.apps.util import ln

import qrcode
import qrcode.image.svg
import svgwrite

import logging

logger = logging.getLogger(__name__)


def abspath(*args):
    """Generates absolute paths"""
    return os.path.abspath(os.path.join(*args))


class QRCode(TemplateView):
    """
    """

    template_name = "qr.svg"

    def get_context_data(self, **kwargs):
        context = super(QRCode, self).get_context_data(**kwargs)
        img = qrcode.make(context["pay_req"], image_factory=qrcode.image.svg.SvgImage)

        with io.BytesIO() as bytes_io:
            img.save(bytes_io)
            context['qr'] = bytes_io.getvalue()

        return context

class PaymentCheck(TemplateView):
    """
    """

    template_name = "payment_check.svg"

    def get_context_data(self, **kwargs):
        context = super(PaymentCheck, self).get_context_data(**kwargs)
        memo = context["memo"]

        count = 0
        while True:
            result = ln.check(memo, node_id=1)
            if result != ln.CHECKPOINT_WAIT:
                break

            # TODO: shutdown if sigterm is caught
            time.sleep(1)
            count += 1
            if count > 10:
                raise Http404("Max time exceeded")

        if result == ln.CHECKPOINT_DONE:
            # post_url = "https://ln.support/p/141/"
            humanized_title = "Payment Sucessful"
        else:
            humanized_title = "Payment ERROR, please try again later"

        dwg = svgwrite.Drawing(size=(500, 2000))
        dwg_title = dwg.add(dwg.g(font_size=22))
        dwg_title.add(
            dwg.text(
                humanized_title,
                (10, 20)
            )
        )

        # dwg_prefix = dwg.add(dwg.g(font_size=14))
        # dwg_prefix.add(
        #     dwg.text(
        #         "Post published ---> ",
        #         (10, 50),
        #     )
        # )

        # dwg_link = dwg.add(dwg.g(font_size=14))
        # dwg_link.add(
        #     dwg.text(
        #         post_url,
        #         (120, 50),
        #         text_decoration="underline"
        #     )
        # )

        link = dwg.add(dwg.a(post_url, target="_top"))
        link.add(dwg_link)

        context['payment_check'] = dwg.tostring()

        return context
