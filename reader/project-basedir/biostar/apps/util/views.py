# Create your views here.
import os
import io

from django import forms
from django.views.generic import  UpdateView, DetailView, TemplateView
from django.contrib.flatpages.models import FlatPage
from django.http import HttpResponseRedirect
from django.conf import settings

import qrcode
import qrcode.image.svg

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
