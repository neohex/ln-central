# Create your views here.
from django.shortcuts import render_to_response
from django.views.generic import TemplateView, DetailView, ListView, FormView, UpdateView
from .models import Post, PostPreview
from django import forms
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, Submit, ButtonHolder
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpRequest
from datetime import datetime
from django.utils.timezone import utc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.exceptions import ValidationError
import re
import logging

import langdetect
from django.template.loader import render_to_string

from common.const import OrderedDict
from common import general_util
from common import json_util

from biostar.apps.util import ln
from biostar.apps.users.models import User


def english_only(text):
    try:
        text.decode('ascii')
    except Exception:
        raise ValidationError('Title may only contain plain text (ASCII) characters')


def valid_language(text):
    supported_languages = settings.LANGUAGE_DETECTION
    if supported_languages:
        lang = langdetect.detect(text)
        if lang not in supported_languages:
            raise ValidationError(
                    'Language "{0}" is not one of the supported languages {1}!'.format(lang, supported_languages))


logger = logging.getLogger(__name__)


def valid_title(text):
    "Validates form input for tags"
    text = text.strip()
    if not text:
        raise ValidationError('Please enter a title')

    if len(text) < 10:
        raise ValidationError('The title is too short')

    words = text.split(" ")
    if len(words) < 3:
        raise ValidationError('More than two words please.')


def valid_tag(text):
    "Validates form input for tags"
    text = text.strip()
    if not text:
        raise ValidationError('Please enter at least one tag')
    if len(text) > 50:
        raise ValidationError('Tag line is too long (50 characters max)')
    words = text.split(",")
    if len(words) > 5:
        raise ValidationError('You have too many tags (5 allowed)')

class PagedownWidget(forms.Textarea):
    TEMPLATE = "pagedown_widget.html"

    def render(self, name, value, attrs=None):
        value = value or ''
        rows = attrs.get('rows', 15)
        klass = attrs.get('class', '')
        params = dict(value=value, rows=rows, klass=klass)
        return render_to_string(self.TEMPLATE, params)


class LongForm(forms.Form):
    FIELDS = "title content post_type tag_val".split()

    POST_CHOICES = [
        (Post.QUESTION, "Question"),
        (Post.META_QUESTION, "Meta (a question/discussion about this website)")
    ]

    title = forms.CharField(
        label="Post Title",
        required=True,
        max_length=200, min_length=10, validators=[valid_title, english_only],
        help_text="Descriptive titles promote better answers.")

    post_type = forms.ChoiceField(
        label="Post Type",
        required=True,
        choices=POST_CHOICES, help_text="Select a post type: Question, Job Offer, Tutorial, Blog, Meta")

    tag_val = forms.CharField(
        label="Post Tags",
        required=True, validators=[valid_tag],
        help_text="Choose one or more tags to match the topic. To create a new tag just type it in and press ENTER.",
    )

    # note: max_length is larger than MAX_MEMO_SIZE because max_length applies before compression
    # max_length is here to guide the user during editing, while MAX_MEMO_SIZE is the final
    # insurance that the memo will fit into the lightning payment
    content = forms.CharField(widget=PagedownWidget, validators=[valid_language],
                              min_length=80, max_length=1100,
                              label="Enter your post below")

    def __init__(self, *args, **kwargs):
        super(LongForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "post-form"
        self.helper.layout = Layout(
            Fieldset(
                'Post Form',
                Field('title'),
                Field('post_type'),
                Field('tag_val'),
                Field('content'),
            ),
            ButtonHolder(
                Submit('submit', 'Preview')
            )
        )

    def clean(self):
        cleaned_data = super(LongForm, self).clean()

        post_preview = PostPreview(
              title=cleaned_data.get('title'),
              content=cleaned_data.get('content'),
              tag_val=cleaned_data.get('tag_val'),
              type=int(cleaned_data.get('post_type')),
              date=general_util.now()
        )

        try:
            serialized = post_preview.serialize_memo()

        except json_util.MemoTooLarge as err:
            raise ValidationError(
                (
                    '%(msg)s. '
                    'Sorry, we are not going to be able to fit this into a lightning payment memo.'
                ),
                code='too_big_serialized',
                params={
                    'max_size': settings.MAX_MEMO_SIZE,
                    'msg': "{0}".format(err)
                    },
            )

        return cleaned_data


class ShortForm(forms.Form):
    FIELDS = ["content"]

    content = forms.CharField(widget=PagedownWidget, min_length=20, max_length=5000,)

    def __init__(self, *args, **kwargs):
        super(ShortForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Post',
                'content',
            ),
            ButtonHolder(
                Submit('submit', 'Preview')
            )
        )


def parse_tags(category, tag_val):
    pass


class NewPost(FormView):
    form_class = LongForm
    template_name = "post_edit.html"

    def get(self, request, *args, **kwargs):
       
        initial = dict()

        if "memo" in kwargs:
            memo = json_util.deserialize_memo(kwargs["memo"])
            for key in "title post_type tag_val content".split():
                initial[key] = memo[key]
        else:
            # Attempt to prefill from GET parameters
            for key in "title post_type tag_val content".split():
                value = request.GET.get(key)
                if value:
                    initial[key] = value

        # here, there used to be code to pre-fill from external session
        form = self.form_class(initial=initial)
        context = {
            'form': form,
            'nodes_list': ln.get_nodes_list(),   # Get LN Nodes list
            'payment_amount': settings.PAYMENT_AMOUNT
        }

        return render(request, self.template_name, context)


    def post(self, request, *args, **kwargs):
        '''
        Authenticated action
        '''

        # Validating the form.
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {'form': form}
            )

        # Valid forms start here.
        data = form.cleaned_data.get

        post_preview = PostPreview(
              title=data('title'),
              content=data('content'),
              tag_val=data('tag_val'),
              type=int(data('post_type')),
              date=general_util.now()
        )

        return HttpResponseRedirect(post_preview.get_absolute_url(memo=post_preview.serialize_memo()))


class NewAnswer(FormView):
    """
    Creates a new post.
    """
    form_class = ShortForm
    template_name = "post_edit.html"
    type_map = dict(answer=Post.ANSWER, comment=Post.COMMENT)
    post_type = None

    def get(self, request, *args, **kwargs):
        initial = {}

        # The parent id.
        pid = int(self.kwargs['pid'])
        # form_class = ShortForm if pid else LongForm
        form = self.form_class(initial=initial)

        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):

        pid = int(self.kwargs['pid'])

        # Find the parent.
        try:
            parent = Post.objects.get(pk=pid)
        except ObjectDoesNotExist, exc:
            logger.error("The post does not exist. Perhaps it was deleted request (Request: %s)", request)
            return HttpResponseRedirect("/")

        # Validating the form.
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        # Valid forms start here.
        data = form.cleaned_data.get

        # Figure out the right type for this new post
        post_type = self.type_map.get(self.post_type)

        # Create a new post.

        # TODO
        # post = Post(
        #     title=parent.title, content=data('content'), author=request.user, type=post_type,
        #     parent=parent,
        # )

        # logger.info("%s created request (Request: %s)", post.get_type_display(), request)
        # post.save()

        return HttpResponseRedirect(post.get_absolute_url())


class EditPost(FormView):
    """
    Edits an existing post.
    """

    # The template_name attribute must be specified in the calling apps.
    template_name = "post_edit.html"
    form_class = LongForm

    def get(self, request, *args, **kwargs):
        initial = {}

        pk = int(self.kwargs['pk'])
        post = Post.objects.get(pk=pk)
        post = auth.post_permissions(request=request, post=post)

        # Check and exit if not a valid edit.
        if not post.is_editable:
            logger.error("This user may not modify the post (Request: %s)", request)
            return HttpResponseRedirect(reverse("home"))

        initial = dict(title=post.title, content=post.content, post_type=post.type, tag_val=post.tag_val)

        # Disable rich editing for preformatted posts
        pre = 'class="preformatted"' in post.content
        form_class = LongForm if post.is_toplevel else ShortForm
        form = form_class(initial=initial)
        return render(request, self.template_name, {'form': form, 'pre': pre})

    def post(self, request, *args, **kwargs):

        pk = int(self.kwargs['pk'])
        post = Post.objects.get(pk=pk)
        post = auth.post_permissions(request=request, post=post)

        # For historical reasons we had posts with iframes
        # these cannot be edited because the content would be lost in the front end
        if "<iframe" in post.content:
            logger.error("This post is not editable because of an iframe! Contact if you must edit it (Request: %s)", request)
            return HttpResponseRedirect(post.get_absolute_url())

        # Check and exit if not a valid edit.
        if not post.is_editable:
            logger.error("This user may not modify the post (Request: %s)", request)
            return HttpResponseRedirect(post.get_absolute_url())

        # Posts with a parent are not toplevel
        form_class = LongForm if post.is_toplevel else ShortForm

        form = form_class(request.POST)
        if not form.is_valid():
            # Invalid form submission.
            return render(request, self.template_name, {'form': form})

        # Valid forms start here.
        data = form.cleaned_data

        # Set the form attributes.
        for field in form_class.FIELDS:
            setattr(post, field, data[field])

        # TODO: fix this oversight!
        post.type = int(data.get('post_type', post.type))

        # This is needed to validate some fields.
        post.save()

        if post.is_toplevel:
            post.add_tags(post.tag_val)

        # Update the last editing user.

        # TODO
        # post.lastedit_user = request.user

        # # Only editing by author bumps the post.
        # if request.user == post.author:
        #     post.lastedit_date = datetime.utcnow().replace(tzinfo=utc)
        # post.save()
        
        logger.info("Post updated (Request: %s)", request)

        return HttpResponseRedirect(post.get_absolute_url())

    def get_success_url(self):
        return reverse("user_details", kwargs=dict(pk=self.kwargs['pk']))

