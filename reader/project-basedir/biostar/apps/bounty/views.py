from django.shortcuts import render
from django.views.generic import  TemplateView

from common.log import logger

class PreviewBountyView(TemplateView):
    template_name = "preview_bounty.html"

    def get_context_data(self, **kwargs):
        context = super(PreviewBountyView, self).get_context_data(**kwargs)
        pid = kwargs["pid"]
        context["pid"] = pid

        logger.debug("Preview for post_id {}".format(pid))  # TODO: Remove

        return context

