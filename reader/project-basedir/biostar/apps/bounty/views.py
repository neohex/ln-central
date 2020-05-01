import time

from django.shortcuts import render
from django.views.generic import  TemplateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, Submit, ButtonHolder

from common import json_util
from biostar.apps.util import ln

from common.log import logger

class BontyForm(forms.Form):
    FIELDS = ["amt"]

    amt = forms.CharField(
        widget=forms.NumberInput,
        label="Ammount (in sats)",
        required=True,
        error_messages={
            'required': "Bounty ammount is required"
        },
        max_length=20, min_length=1,
        validators=[],
        help_text="Ammount of sats to start or increase the bounty",
    )

    def __init__(self, *args, **kwargs):
        super(BontyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Bounty',
                'amt'
            ),
            ButtonHolder(
                Submit('submit', 'Preview')
            )
        )


class BountyFormView(TemplateView):
    template_name = "bounty_form.html"
    form_class = BontyForm

    def get_context_data(self, **kwargs):
        context = super(BountyFormView, self).get_context_data(**kwargs)

        pid = kwargs["pid"]
        context["pid"] = pid

        logger.debug("New bounty form for post_id {}".format(pid))

        return context

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial={"amt": 10000})

        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
        except Exception as e:
            logger.exception(e)
            raise

        # Validating the form.
        form = self.form_class(request.POST)
        if not form.is_valid():
            try:
                context = self.get_context_data(**kwargs)
            except Exception as e:
                logger.exception(e)
                raise

            context['form'] = form
            context['errors_detected'] = True

            return render(
                request,
                self.template_name,
                context
            )

        pid = context["pid"]
        amt = form.cleaned_data.get("amt")

        logger.debug("Bounty ammount is {} for post_id {}".format(amt, pid))
        memo = {
            "post_id": pid,
            "ammount": amt,
            "unixtime": int(time.time())
        }

        memo_serialized = json_util.serialize_memo(memo)

        return HttpResponseRedirect(reverse("bounty-publish", kwargs=dict(memo=memo_serialized)))


class BountyPublishView(TemplateView):
    template_name = "bounty_publish.html"

    def get_context_data(self, **kwargs):
        context = super(BountyPublishView, self).get_context_data(**kwargs)

        # TODO: move this to a common lib
        nodes_list = ln.get_nodes_list()

        if len(nodes_list) == 0:
            return context

        if 'node_id' not in context:
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
        context["next_node_url"] = reverse(
            "bounty-publish-node-selected",  # TODO: when refactored, take as argument
            kwargs=dict(
                memo=context["memo"],
                node_id=next_node_id
            )
        )
        context["open_channel_url"] = reverse(
            "open-channel-node-selected",
            kwargs=dict(
                node_id=next_node_id
            )
        )

        return context

    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
        except Exception as e:
            logger.exception(e)
            raise

        return render(request, self.template_name, context)
