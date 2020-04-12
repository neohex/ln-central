from django.shortcuts import render

from django.views.generic import  TemplateView

class NewBountyView(TemplateView):
    template_name = "new_bounty.html"
