"""biostar_writer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
import lner.views

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'ln/list', lner.views.LightningNodeViewSet)
router.register(r'ln/addinvoice', lner.views.CreateInvoiceViewSet, basename='invoice')
router.register(r'ln/check', lner.views.CheckPaymentViewSet, basename='check')
router.register(r'ln/verifymessage', lner.views.VerifyMessageViewSet, basename='verifymessage')

urlpatterns = []

urlpatterns = format_suffix_patterns(urlpatterns) + [
	url(r'^', include(router.urls)),
]
