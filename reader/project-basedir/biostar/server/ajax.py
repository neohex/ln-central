__author__ = 'ialbert'
import json, traceback
from braces.views import JSONResponseMixin
from biostar.apps.posts.models import Post, Vote
from biostar.apps.users.models import User
from django.views.generic import View
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from functools import partial
from django.db import transaction
from django.db.models import Q, F


def json_response(adict, **kwd):
    """Returns a http response in JSON format from a dictionary"""
    return HttpResponse(json.dumps(adict), **kwd)


from common.log import logger


def ajax_msg(msg, status, **kwargs):
    payload = dict(status=status, msg=msg)
    payload.update(kwargs)
    return json_response(payload)


ajax_success = partial(ajax_msg, status='success')
ajax_error = partial(ajax_msg, status='error')


class ajax_error_wrapper(object):
    """
    Used as decorator to trap/display  errors in the ajax calls
    """

    def __init__(self, f):
        self.f = f

    def __call__(self, request):
        try:
            if request.method != 'POST':
                return ajax_error('POST method must be used.')

            value = self.f(request)
            return value
        except Exception, exc:
            traceback.print_exc()
            return ajax_error('Error: %s' % exc)

