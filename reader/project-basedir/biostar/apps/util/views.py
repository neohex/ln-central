# Create your views here.
import os
import io
import time

from django import forms
from django.views.generic import  UpdateView, DetailView, TemplateView
from django.http import HttpResponseRedirect
from django.http import Http404
from django.conf import settings
from django.core.urlresolvers import reverse

from biostar.apps.util import ln
from biostar.apps.posts.models import Post

import qrcode
import qrcode.image.svg
import svgwrite

from common.log import logger


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
        node_id = context["node_id"]

        count = 0
        while True:
            result = ln.check_payment(memo, node_id=node_id)
            checkpoint_value = result["checkpoint_value"]
            conclusion = ln.gen_check_conclusion(checkpoint_value, node_id=node_id, memo=memo)

            if conclusion != ln.CHECKPOINT_WAIT:
                break

            # TODO: shutdown if sigterm is caught
            time.sleep(1)
            count += 1
            if count > 10:
                raise Http404("Max time exceeded")

        dwg = svgwrite.Drawing(size=(500, 2000))

        if conclusion == ln.CHECKPOINT_DONE:
            post_id = result["performed_action_id"]
            print(post_id)

            action_type = result["performed_action_type"]

            if action_type == "post":
                action_title = "Post published"
            elif action_type == "upvote":
                action_title = "Vote casted"
            else:
                action_title = "Action compleated"

            post = Post.objects.get(id=post_id)
            post_url = 'https://{}{}'.format(settings.SITE_DOMAIN, post.get_absolute_url())

            dwg_title = dwg.add(dwg.g(font_size=50))
            dwg_title.add(
                dwg.text(
                    "Payment Sucessful",
                    (10, 50)
                )
            )

            dwg_subtitle = dwg.add(dwg.g(font_size=14))
            dwg_subtitle.add(
                dwg.text(
                    "{} ---> Post ID is {}".format(action_title, post_id),
                    (10, 100),
                )
            )

            dwg_link = dwg.add(dwg.g(font_size=14))
            dwg_link.add(
                dwg.text(
                    "{}".format(post_url),
                    (70, 130),
                )
            )

            link = dwg.add(dwg.a(post_url, target="_top"))
            link.add(dwg_link)
        else:
            dwg_title = dwg.add(dwg.g(font_size=20))
            dwg_title.add(
                dwg.text(
                    "Payment ERROR, please try again later",
                    (10, 50)
                )
            )

        context['payment_check'] = dwg.tostring()

        return context


class ChannelOpenView(TemplateView):
    """
    """

    template_name = "channel_open.html"

    def get_context_data(self, **kwargs):
        context = super(ChannelOpenView, self).get_context_data(**kwargs)
        nodes_list = ln.get_nodes_list()

        # TODO: modularize getting best node and name lookup

        if 'node_id' not in context:
            # best node
            node_with_top_score = nodes_list[0]
            for node in nodes_list:
                if node["qos_score"] > node_with_top_score["qos_score"]:
                    node_with_top_score = node

            node_id = node_with_top_score["id"]

            context["node_id"] = str(node_id)
        else:
            node_id = int(context["node_id"])

        # Lookup the node name
        node_name = "Unknown"
        list_pos = 0
        for pos, n in enumerate(nodes_list):
            if n["id"] == node_id:
                node_name = n["node_name"]
                list_pos = pos

                node_key = n["node_key"]
                if n["is_tor"]:
                    connect = n["connect_tor"]
                else:
                    connect = n["connect_ip"]

        context["node_name"] = node_name
        context["node_key"] = node_key
        context["connect"] = connect

        next_node_id = nodes_list[(list_pos + 1) % len(nodes_list)]["id"]
        context["next_node_url"] = reverse("open-channel-node-selected", kwargs=dict(node_id=next_node_id))


        return context
