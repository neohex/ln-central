# Create your views here.
import re
import json
import langdetect

from django.shortcuts import render_to_response
from django.views.generic import TemplateView, DetailView, ListView, FormView, UpdateView
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

from django.template.loader import render_to_string

from common.const import OrderedDict
from common import general_util
from common import json_util
from common import html_util
from common import validators

from biostar.apps.util import ln
from biostar.apps.users.models import User
from biostar.apps.posts.models import PostPreview, Post

from common.log import logger

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
        max_length=200, min_length=10,
        validators=[valid_title, english_only, validators.validate_signable_field],
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

        parent_post_id = cleaned_data.get("parent_post_id")

        if parent_post_id:

            # Find the parent.
            try:
                parent = Post.objects.get(pk=parent_post_id)
            except ObjectDoesNotExist, exc:
                raise ValidationError(
                    "Parent post {} does not exist. Perhaps it was deleted request".format(
                        parent_post_id
                    )
                )

            post_preview = PostPreview(
                parent_post_id = parent_post_id,
                title = parent.title,
                tag_val = parent.tag_val,
                tag_value = html_util.split_tags(parent.tag_val),
                content=cleaned_data.get('content'),
                type=int(cleaned_data.get('post_type')),
                date=general_util.now()
            )
        else:
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
    FIELDS = ["content", "parent_post_id"]

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


class SignMessageForm(forms.Form):
    FIELDS = ["signature"]

    signature = forms.CharField(
        widget=forms.Textarea,
        label="Signature",
        required=True,
        error_messages={
            'required': (
                "Signature is optional, yet you clicked \"Check\" and did not provide any Signature. "
                "If you want to post unsigned then click on \"Get Invoice\" at the bottom of this page"
            )
        },
        max_length=200, min_length=10,
        validators=[validators.pre_validate_signature],
        help_text="JSON output of the signmessage command or just text of the signature")

    def __init__(self, *args, **kwargs):
        if "memo" in kwargs:
            memo = kwargs.pop("memo")
        else:
            memo = kwargs.get("initial").get("memo")

        super(SignMessageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('signature', rows="4"),
            ButtonHolder(
                Submit('submit', 'Check')
            )
        )

        self.helper.form_action = reverse(
            "post-preview",
            kwargs=dict(memo=memo)
        )

def parse_tags(category, tag_val):
    pass


class NewPost(FormView):
    form_class = LongForm
    template_name = "post_edit.html"


    def get_context_data(self, **kwargs):
        context = super(NewPost, self).get_context_data(**kwargs)
        context['nodes_list'] = [n["node_name"] for n in ln.get_nodes_list()]
        return context

    def get(self, request, *args, **kwargs):

        initial = dict()

        if "memo" in kwargs:
            memo = json_util.deserialize_memo(kwargs["memo"])

            if "parent_post_id" in memo:
                expected_memo_keys = ["parent_post_id", "post_type", "content"]
                self.form_class = ShortForm
            else:
                expected_memo_keys = ["title", "post_type", "tag_val", "content"]

            for key in expected_memo_keys:
                initial[key] = memo[key]
        else:
            # Attempt to prefill from GET parameters
            for key in "title post_type tag_val content".split():
                value = request.GET.get(key)
                if value:
                    initial[key] = value

        context = self.get_context_data(**kwargs)
        context['form'] = self.form_class(initial=initial)
        context['errors_detected'] = False

        return render(request, self.template_name, context)


    def post(self, request, *args, **kwargs):
        if "memo" in kwargs:
            post_preview = PostPreview()

            # Some data comes from memo
            memo = json_util.deserialize_memo(kwargs["memo"])

            if "parent_post_id" in memo:
                self.form_class = ShortForm

                parent_post_id = memo["parent_post_id"]

                # Find the parent.
                try:
                    parent = Post.objects.get(pk=parent_post_id)
                except ObjectDoesNotExist, exc:
                    logger.error("The post does not exist. Perhaps it was deleted request (Request: %s)", request)
                    return HttpResponseRedirect("/")

                post_preview.parent_post_id = parent_post_id
                post_preview.title = parent.title
                post_preview.tag_val = parent.tag_val
                post_preview.tag_value = html_util.split_tags(parent.tag_val)
            else:
                post_preview.title = memo["title"]
                post_preview.tag_val = memo["tag_val"]
                post_preview.tag_value = html_util.split_tags(memo["tag_val"])

            post_preview.status = Post.OPEN
            post_preview.type = memo["post_type"]
            post_preview.date = datetime.utcfromtimestamp(memo["unixtime"]).replace(tzinfo=utc)

        # Validating the form.
        form = self.form_class(request.POST)
        if not form.is_valid():
            context = self.get_context_data(**kwargs)
            context['form'] = form
            context['errors_detected'] = True

            return render(
                request,
                self.template_name,
                context
            )

        if "memo" in kwargs:
            # Only new data comes from the HTML form
            post_preview.content = form.cleaned_data.get("content")
            post_preview.html = html_util.parse_html(post_preview.content)
        else:
            # Valid forms start here.
            data = form.cleaned_data

            # All data comes from the HTML form
            post_preview = PostPreview(
                  title=data.get('title'),
                  content=data.get('content'),
                  tag_val=data.get('tag_val'),
                  type=int(data.get('post_type')),
                  date=general_util.now()
            )

        return HttpResponseRedirect(post_preview.get_absolute_url(memo=post_preview.serialize_memo()))

class PostPreviewView(FormView):
    """
    Shows preview of the post and takes an optional signature
    """

    template_name = "post_preview.html"
    form_class = SignMessageForm

    def get_form_kwargs(self):
        view_obj = super(PostPreviewView, self).get_context_data().get("view")
        memo = view_obj.kwargs["memo"]

        return {
            "memo": memo
        }

    def get_model(self, memo):

        post_preview = PostPreview()
        if "parent_post_id" in memo:
            parent_post_id = memo["parent_post_id"]

            # Find the parent.
            try:
                parent = Post.objects.get(pk=parent_post_id)
            except ObjectDoesNotExist, exc:
                logger.error("The post does not exist. Perhaps it was deleted request (Request: %s)", request)
                return HttpResponseRedirect("/")

            post_preview.parent_post_id = parent_post_id
            post_preview.title = parent.title
            post_preview.tag_val = parent.tag_val
            post_preview.tag_value = html_util.split_tags(parent.tag_val)

        else:
            post_preview.title = memo["title"]
            post_preview.tag_val = memo["tag_val"]
            post_preview.tag_value = html_util.split_tags(memo["tag_val"])

        post_preview.status = Post.OPEN
        post_preview.type = memo["post_type"]
        post_preview.content = memo["content"]
        post_preview.html = html_util.parse_html(memo["content"])
        post_preview.date = datetime.utcfromtimestamp(memo["unixtime"]).replace(tzinfo=utc)

        post_preview.memo = post_preview.serialize_memo()

        post_preview.clean_fields()

        return post_preview

    def get_context_data(self, **kwargs):

        context = super(PostPreviewView, self).get_context_data(**kwargs)

        view_obj = context.get("view")
        memo_serialized = view_obj.kwargs["memo"]

        memo = validators.validate_memo(
            json_util.deserialize_memo(memo_serialized)
        )

        signature = kwargs.get("signature")
        if signature:
            result = ln.verifymessage(memo=json.dumps(memo, sort_keys=True), sig=signature)
            if result["valid"]:
                identity_pubkey = result["identity_pubkey"]
                context['user'] = User(id=1, pubkey=identity_pubkey)
                memo["sig"] = signature  # add signature to memo

        if "sig" not in memo:
            context['user'] = User(id=1, pubkey="Unknown")

        post_preview = self.get_model(memo)
        context['post'] = post_preview
        context['publish_url'] = post_preview.get_publish_url(
            memo=json_util.serialize_memo(memo)
        )

        return context


    def post(self, request, *args, **kwargs):
        """
        Post is used when checking signature
        """

        signature = request.POST.get("signature")
        kwargs["signature"] = signature

        view = super(PostPreviewView, self).get(request, *args, **kwargs)
        view_obj = super(PostPreviewView, self).get_context_data().get("view")
        memo_serialized = view_obj.kwargs["memo"]

        memo = validators.validate_memo(
            json_util.deserialize_memo(memo_serialized)
        )

        form = self.form_class(request.POST, memo=memo_serialized)

        if form.is_valid():
            if signature:
                result = ln.verifymessage(memo=json.dumps(memo, sort_keys=True), sig=signature)
                if not result["valid"]:
                    # Signature is invalid

                    ## See: https://github.com/alevchuk/ln-central/issues/27
                    # self.form_class.add_error(
                    #     "signature",
                    #     ValidationError("Signature is invalid. Try signing latest preview data or delete signature to be anonymous.")
                    # )

                    post_preview = self.get_model(memo)

                    context = {
                        "post": post_preview,
                        "form": form,
                        "user": User.objects.get(pubkey="Unknown"),
                        "errors_detected": True,
                        "show_error_summary": True,
                        "error_summary_list": [
                            "Signature is invalid. Try signing latest preview data or delete signature to be anonymous."
                        ]
                    }
                else:
                    context = self.get_context_data(**kwargs)
                    context["form"] = form
                    context["errors_detected"] = False
            else:
                context = self.get_context_data(**kwargs)
                context["form"] = form
                context["errors_detected"] = False
        else:
            # Form errors detected
            post_preview = self.get_model(memo)

            context = self.get_context_data(**kwargs)
            context["form"] = form
            context["errors_detected"] = True

        return render(request, self.template_name, context)


class NewAnswer(FormView):
    """
    Creates a new post.
    """

    form_class = ShortForm
    template_name = "post_edit.html"
    type_map = dict(answer=Post.ANSWER, comment=Post.COMMENT)
    post_type = None

    def get_context_data(self, **kwargs):
        context = super(NewAnswer, self).get_context_data(**kwargs)
        context['nodes_list'] = [n["node_name"] for n in ln.get_nodes_list()]
        return context

    def post(self, request, *args, **kwargs):
        """
        This gets the initial "new answer" request, before the get method
        if everything looks good then we generate the memo (with parent post id)
        and re-direct to preview. If there are errors, we also render this
        back to the user directly from here. See `if not form.is_valid()`
        """

        parent_post_id = int(self.kwargs['pid'])

        # URL sets the type for this new post
        post_type = self.type_map.get(self.post_type)
        assert post_type in [Post.ANSWER, Post.COMMENT], "I only support Answers and Comment types, got: {}".format(post_type)

        # Find the parent.
        try:
            parent = Post.objects.get(pk=parent_post_id)
        except ObjectDoesNotExist, exc:
            logger.error("The post does not exist. Perhaps it was deleted request (Request: %s)", request)
            return HttpResponseRedirect("/")

        # Validating the form.
        form = self.form_class(request.POST)
        if not form.is_valid():
            context = self.get_context_data(**kwargs)
            context["form"] = form
            context["errors_detected"] = True
            return render(request, self.template_name, context)

        # Valid forms start here
        content = form.cleaned_data.get("content")

        post_preview = PostPreview()
        post_preview.parent_post_id = parent_post_id
        post_preview.title = parent.title
        post_preview.tag_val = parent.tag_val
        post_preview.tag_value = html_util.split_tags(parent.tag_val)
        post_preview.status = Post.OPEN
        post_preview.type = post_type
        post_preview.content = content
        post_preview.html = html_util.parse_html(content)
        post_preview.date = general_util.now()
        post_preview.memo = post_preview.serialize_memo()

        post_preview.clean_fields()

        return HttpResponseRedirect(post_preview.get_absolute_url(memo=post_preview.memo))



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


class VotePublishView(TemplateView):
    """
    """

    template_name = "vote_publish.html"

    def get_context_data(self, **kwargs):
        context = super(VotePublishView, self).get_context_data(**kwargs)
        nodes_list = ln.get_nodes_list()

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
            "vote-publish-node-selected",
            kwargs=dict(
                memo=context["memo"],
                node_id=next_node_id
            )
        )

        try:
            details = ln.add_invoice(context["memo"], node_id=node_id)
        except ln.LNUtilError as e:
            logger.excetion(e)
            return HttpResponseNotFound(
                "<h1>Command for <b>addinvoice</b> failed or timed-out. "
                "Please refresh this page.</h1>"
            )

        context['pay_req'] = details['pay_req']
        context['payment_amount'] = settings.PAYMENT_AMOUNT

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        memo = context["memo"]

        return super(VotePublishView, self).get(request, *args, **kwargs)
