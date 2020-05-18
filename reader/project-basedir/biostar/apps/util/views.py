# Create your views here.
import os
import io
import time

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, Submit, ButtonHolder

from django import forms
from django.views.generic import  UpdateView, DetailView, TemplateView
from django.http import Http404
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render

from biostar.apps.util import ln
from biostar.apps.posts.models import Post
from biostar.apps.bounty.models import Bounty, BountyAward

import qrcode
import qrcode.image.svg
import svgwrite

from common import validators
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

        if len(nodes_list) == 0:
            raise ln.LNUtilError("No nodes found")

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
        node_key = "Unknown"
        connect = "Unknown"

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


class TakeCustodyInvoiceForm(forms.Form):
    FIELDS = ["invoice"]

    invoice = forms.CharField(
        widget=forms.TextInput,
        label="Lightning Invoice",
        required=True,
        error_messages={
            'required': "Invoice is required"
        },
        max_length=settings.MAX_MEMO_SIZE, min_length=5,
        validators=[],
        help_text="Invoice to take custody of the sats won",
    )

    def __init__(self, *args, **kwargs):
        super(TakeCustodyInvoiceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Invoice',
                'invoice'
            ),
            ButtonHolder(
                Submit('submit', 'Next')
            )
        )

class TakeCustodySignForm(forms.Form):
    FIELDS = ["invoice", "signature"]

    invoice = forms.CharField(
        widget=forms.TextInput,
        label="Lightning Invoice",
        required=True,
        error_messages={
            'required': "Invoice is required"
        },
        max_length=settings.MAX_MEMO_SIZE, min_length=5,
        validators=[],
        help_text="Invoice to take custody of the sats won",
    )

    signature = forms.CharField(
        widget=forms.Textarea,
        label="Signature",
        required=True,
        error_messages={
            'required': (
                "Signature is required"
            )
        },
        max_length=200, min_length=10,
        validators=[validators.pre_validate_signature],
        help_text="JSON output of the signmessage command or just text of the signature")

    def __init__(self, *args, **kwargs):
        super(TakeCustodySignForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Fieldset(
                'Invoice with signature',
                'invoice'
            ),
            Field('signature', rows="4"),
            ButtonHolder(
                Submit('submit', 'Initiate Payment')
            )
        )


class TakeCustodyView(TemplateView):
    """
    """

    template_name = "take_custody.html"
    form_class1 = TakeCustodyInvoiceForm
    form_class2 = TakeCustodySignForm

    def get_context_data(self, **kwargs):
        context = super(TakeCustodyView, self).get_context_data(**kwargs)
        award_id = int(context["award_id"])

        nodes_list = ln.get_nodes_list()

        if len(nodes_list) == 0:
            raise ln.LNUtilError("No nodes found")

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

        context["node_name"] = node_name

        next_node_id = nodes_list[(list_pos + 1) % len(nodes_list)]["id"]

        context["next_node_url"] = reverse("take-custody-node-selected", kwargs=dict(node_id=next_node_id, award_id=award_id))

        # Lookup author and other bounty details
        award = BountyAward.objects.get(id=award_id)
        context["post"] = award.post

        # TODO: put into a shard function get_bounty_sats
        bounty_sats = 0

        for b in Bounty.objects.filter(post_id=award.post.parent.id, is_active=True, is_payed=False):
            bounty_sats += b.amt

        context["amt"] = bounty_sats

        return context


    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
        except Exception as e:
            logger.exception(e)
            return render(request, self.template_name, {})

        form1 = self.form_class1(initial={"invoice": ""})
        context['invoice_form'] = form1

        return render(request, self.template_name, context)


    def post(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
        except Exception as e:
            logger.exception(e)
            raise

        invoice_pre_validation = request.POST.get("invoice")
        sign_pre_validation = request.POST.get("signature")

        if not invoice_pre_validation:
            # Invoice not provided, back to first form to get invoice

            form1 = self.form_class1(request.POST)
            context['invoice_form'] = form1
            context['errors_detected'] = True

        elif not sign_pre_validation:
            # Time to sign
            form2 = self.form_class2(initial={"invoice": invoice_pre_validation, "signature": ""})
            context['sign_form'] = form2
            context['invoice'] = invoice_pre_validation

        elif invoice_pre_validation and sign_pre_validation:
            # Got everithing
            form2 = self.form_class2(request.POST)
            context['sign_form'] = form2
            context['invoice'] = invoice_pre_validation

            error_summary_list = []

            if not form2.is_valid():
                context['errors_detected'] = True
            else:
                # TODO: make API call and report back the results, potentially populating error_summary_list
                error_summary_list.append("This type of pyament is not yet implemented")

                if len(error_summary_list) > 0:
                    context['errors_detected'] = True
                    context["show_error_summary"] = True
                    context["error_summary_list"] = error_summary_list

        else:
            raise ln.LNUtilError("Invaild state")

        return render(request, self.template_name, context)
