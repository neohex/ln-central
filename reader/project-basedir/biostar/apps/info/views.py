from django.shortcuts import render

from django.views.generic import TemplateView


class FaqView(TemplateView):
    template_name = "faq.html"



class AboutView(TemplateView):
    template_name = "about.html"



class PolicyView(TemplateView):
    template_name = "policy.html"



class RSSView(TemplateView):
    template_name = "rss_info.html"
