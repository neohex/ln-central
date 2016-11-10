# Create your views here.
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import TemplateView, DetailView, ListView, FormView, UpdateView
from .models import Post
from django import forms
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, Submit, ButtonHolder
from django.http import HttpResponseRedirect, HttpRequest
from django.contrib import messages
from . import auth
from braces.views import LoginRequiredMixin
from datetime import datetime
from django.utils.timezone import utc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from biostar.const import OrderedDict
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import re
import logging

import langdetect
from django.template.loader import render_to_string

import requests
import json
import urllib
import random
import string

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


def valid_github_repo(text):
    "Validates form input"
    text = text.strip()
    if not text:
        raise ValidationError('Please enter a GitHub repo')

    if not re.match("^[A-Za-z0-9_.-]+$", text):
        raise ValidationError('Please enter a valid GitHub repo name')

def valid_github_user(text):
    "Validates form input"
    text = text.strip()
    if not text:
        raise ValidationError('Please enter a GitHub user or organization')

    if not re.match("^[A-Za-z0-9_.-]+$", text):
        raise ValidationError('Please enter a valid GitHub user or organization')


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


class GitHubAPI(object):
    @staticmethod
    def request_access_token(redirect_uri, user_profile):
        '''
        Redirect user to request GitHub access
        - Takes the URI string to which the user will be redirected back after GitHub authorization
        - Returns the URI string that will be used to form the HTTP redirect to GitHub
        '''
        git_authorize_state = ''.join([random.choice(string.ascii_uppercase + string.digits) for _ in range(20)])
        git_authorize_state += datetime.isoformat(datetime.now()) 

        user_profile.github_csrf_state = git_authorize_state
        user_profile.save()

        authorize_params = {
            'client_id': settings.GITHUB_APP_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'public_repo',
            'state': git_authorize_state
            }

        return 'https://github.com/login/oauth/authorize?' + urllib.urlencode(authorize_params)

    @staticmethod
    def check_access_token(token):
        api_req_url = 'https://api.github.com/applications/{}/tokens/{}'.format(
            settings.GITHUB_APP_CLIENT_ID, token)
        resp = requests.get(api_req_url,
            auth=requests.auth.HTTPBasicAuth(settings.GITHUB_APP_CLIENT_ID, settings.GITHUB_APP_CLIENT_SECRET))
        resp_json = resp.json()

        if 'public_repo' in resp_json.get('scopes', []):
            return True

        return False
    
    @staticmethod
    def open_issue(access_token, repo_user, repo_name, issue_title, issue_body):
        '''
        Open GitHub Issue
        '''

        api_req_url = 'https://api.github.com/repos/{}/{}/issues'.format(repo_user, repo_name)

        resp = requests.post(
            api_req_url,
            data=json.dumps({"title": issue_title, "body": issue_body}),
            headers={'Authorization': 'token ' + access_token})

        resp_json = resp.json()

        return resp_json['number']

    @staticmethod
    def edit_issue(access_token, issue_number, repo_user, repo_name, issue_title, issue_body):
        '''
        Edit GitHub Issue
        '''
        api_req_url = 'https://api.github.com/repos/{}/{}/issues/{}'.format(repo_user, repo_name, issue_number)

        resp = requests.patch(
            api_req_url,
            data=json.dumps({"title": issue_title, "body": issue_body}),
            headers={'Authorization': 'token ' + access_token})

        resp_json = resp.json()

        return resp_json['number']


class PagedownWidget(forms.Textarea):
    TEMPLATE = "pagedown_widget.html"

    def render(self, name, value, attrs=None):
        value = value or ''
        rows = attrs.get('rows', 15)
        klass = attrs.get('class', '')
        params = dict(value=value, rows=rows, klass=klass)
        return render_to_string(self.TEMPLATE, params)

class GithubIssuePreviewWidget(forms.Textarea):
    TEMPLATE = "github_issue_preview_widget.html"

    def render(self, name, value, attrs=None):
        value = value or ''
        name = name or ''
        params = dict(value=value, name=name)
        return render_to_string(self.TEMPLATE, params)


class GithubIssueForm(forms.Form):
    FIELDS = "repo_user repo_name title content".split()

    repo_user = forms.CharField(
        label="GitHub User or Organization",
        max_length=200, min_length=2, validators=[english_only, valid_github_user],
        help_text='E.g. <a href="https://github.com/ialbert">ialbert</a>')

    repo_name = forms.CharField(
        label="GitHub Repository Name",
        max_length=200, min_length=1, validators=[english_only, valid_github_repo],
        help_text='E.g. <a href="https://github.com/ialbert/biostar-central">biostar-central</a>')

    title = forms.CharField(
        widget=GithubIssuePreviewWidget,
        label="GitHub Issue Title",
        max_length=200, min_length=10, validators=[valid_title, english_only])

    content = forms.CharField(
        validators=[valid_language],
        widget=GithubIssuePreviewWidget,
        min_length=80, max_length=15000,
        label="GitHub Issue comment",
        help_text="Body of the Question will appear as the first comment in the Issue")

    def __init__(self, *args, **kwargs):
        super(GithubIssueForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "post-form"
        self.helper.layout = Layout(
            Fieldset(
                'Open GitHub Issue',
                Field('repo_user'),
                Field('repo_name'),
                Field('title'),
                Field('content'),
            ),
            ButtonHolder(
                Submit('submit', 'Submit')
            )
        )


class LongForm(forms.Form):
    FIELDS = "title content post_type tag_val".split()

    POST_CHOICES = [(Post.QUESTION, "Question"),
                    (Post.JOB, "Job Ad"),
                    (Post.TUTORIAL, "Tutorial"), (Post.TOOL, "Tool"),
                    (Post.FORUM, "Forum"), (Post.NEWS, "News"),
                    (Post.BLOG, "Blog"), (Post.PAGE, "Page")]

    title = forms.CharField(
        label="Post Title",
        max_length=200, min_length=10, validators=[valid_title, english_only],
        help_text="Descriptive titles promote better answers.")

    post_type = forms.ChoiceField(
        label="Post Type",
        choices=POST_CHOICES, help_text="Select a post type: Question, Forum, Job, Blog")

    tag_val = forms.CharField(
        label="Post Tags",
        required=True, validators=[valid_tag],
        help_text="Choose one or more tags to match the topic. To create a new tag just type it in and press ENTER.",
    )

    content = forms.CharField(widget=PagedownWidget, validators=[valid_language],
                              min_length=80, max_length=15000,
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
                Submit('submit', 'Submit')
            )
        )


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
                Submit('submit', 'Submit')
            )
        )


def parse_tags(category, tag_val):
    pass


@login_required
@csrf_exempt
def external_post_handler(request):
    "This is used to pre-populate a new form submission"
    import hmac

    user = request.user
    home = reverse("home")
    name = request.REQUEST.get("name")

    if not name:
        messages.error(request, "Incorrect request. The name parameter is missing")
        return HttpResponseRedirect(home)

    try:
        secret = dict(settings.EXTERNAL_AUTH).get(name)
    except Exception, exc:
        logger.error(exc)
        messages.error(request, "Incorrect EXTERNAL_AUTH settings, internal exception")
        return HttpResponseRedirect(home)

    if not secret:
        messages.error(request, "Incorrect EXTERNAL_AUTH, no KEY found for this name")
        return HttpResponseRedirect(home)

    content = request.REQUEST.get("content")
    submit = request.REQUEST.get("action")
    digest1 = request.REQUEST.get("digest")
    digest2 = hmac.new(secret, content).hexdigest()

    if digest1 != digest2:
        messages.error(request, "digests does not match")
        return HttpResponseRedirect(home)

    # auto submit the post
    if submit:
        post = Post(author=user, type=Post.QUESTION)
        for field in settings.EXTERNAL_SESSION_FIELDS:
            setattr(post, field, request.REQUEST.get(field, ''))
        post.save()
        post.add_tags(post.tag_val)
        return HttpResponseRedirect(reverse("post-details", kwargs=dict(pk=post.id)))

    # pre populate the form
    sess = request.session
    sess[settings.EXTERNAL_SESSION_KEY] = dict()
    for field in settings.EXTERNAL_SESSION_FIELDS:
        sess[settings.EXTERNAL_SESSION_KEY][field] = request.REQUEST.get(field, '')

    return HttpResponseRedirect(reverse("new-post"))


class NewPost(LoginRequiredMixin, FormView):
    form_class = LongForm
    template_name = "post_edit.html"

    def get(self, request, *args, **kwargs):
        initial = dict()

        # Attempt to prefill from GET parameters
        for key in "title tag_val content".split():
            value = request.GET.get(key)
            if value:
                initial[key] = value


        # Attempt to prefill from external session
        sess = request.session
        if settings.EXTERNAL_SESSION_KEY in sess:
            for field in settings.EXTERNAL_SESSION_FIELDS:
                initial[field] = sess[settings.EXTERNAL_SESSION_KEY].get(field)
            del sess[settings.EXTERNAL_SESSION_KEY]

        form = self.form_class(initial=initial)
        return render(request, self.template_name, {'form': form})


    def post(self, request, *args, **kwargs):
        # Validating the form.
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        # Valid forms start here.
        data = form.cleaned_data.get

        title = data('title')
        content = data('content')
        post_type = int(data('post_type'))
        tag_val = data('tag_val')

        post = Post(
            title=title, content=content, tag_val=tag_val,
            author=request.user, type=post_type,
        )
        post.save()

        # Triggers a new post save.
        post.add_tags(post.tag_val)

        messages.success(request, "%s created" % post.get_type_display())
        return HttpResponseRedirect(post.get_absolute_url())


class NewAnswer(LoginRequiredMixin, FormView):
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
            messages.error(request, "The post does not exist. Perhaps it was deleted")
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
        post = Post(
            title=parent.title, content=data('content'), author=request.user, type=post_type,
            parent=parent,
        )

        messages.success(request, "%s created" % post.get_type_display())
        post.save()

        return HttpResponseRedirect(post.get_absolute_url())


class EditPost(LoginRequiredMixin, FormView):
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
            messages.error(request, "This user may not modify the post")
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
            messages.error(request, "This post is not editable because of an iframe! Contact if you must edit it")
            return HttpResponseRedirect(post.get_absolute_url())

        # Check and exit if not a valid edit.
        if not post.is_editable:
            messages.error(request, "This user may not modify the post")
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
        post.lastedit_user = request.user

        # Only editing by author bumps the post.
        if request.user == post.author:
            post.lastedit_date = datetime.utcnow().replace(tzinfo=utc)

        post.save()
        messages.success(request, "Post updated")

        if settings.GITHUB_ISSUE_OPENING and post.github_issue_number is not None:
            # Get GitHub token
            if request.user.profile.github_access_token is not None:

                access_token = request.user.profile.github_access_token
                if GitHubAPI.check_access_token(token=access_token):

                    issue_body = render(
                        request,
                        GithubIssue.issue_body_template_name,
                        {
                            'main_body': post.content,
                            'post_url': settings.CALLBACK_URL_BASE + post.get_absolute_url(),
                            'author': post.author },
                        content_type='text/plain')

                    # Edit GitHub Issue
                    GitHubAPI.edit_issue(
                        access_token=access_token,
                        issue_number=post.github_issue_number,
                        repo_user=post.github_repo_user,
                        repo_name=post.github_repo_name,
                        issue_title=post.title,
                        issue_body=issue_body.content)

                    messages.success(request, "GitHub Issue updated")

                    return HttpResponseRedirect(post.get_absolute_url())

            #
            # Redirect user to request GitHub access
            #

            redirect_uri = (
                    '{}/p/github/issue/{}/?'.format(settings.CALLBACK_URL_BASE, post.id) +
                    urllib.urlencode({'repo_user': post.github_repo_user, 'repo_name': post.github_repo_name}))

            return redirect(GitHubAPI.request_access_token(
                redirect_uri=redirect_uri,
                user_profile=request.user.profile))

        

        return HttpResponseRedirect(post.get_absolute_url())

    def get_success_url(self):
        return reverse("user_details", kwargs=dict(pk=self.kwargs['pk']))


class GithubIssue(LoginRequiredMixin, FormView):
    """
    Open a GitHub issue 
    """

    # The template_name attribute must be specified in the calling apps.
    template_name = "github_issue.html"
    issue_body_template_name = "github_issue_body.md"
    form_class = GithubIssueForm

    def get(self, request, *args, **kwargs):
        pk = int(self.kwargs['pk'])
        post = Post.objects.get(pk=pk)
        post = auth.post_permissions(request=request, post=post)

        initial = dict(
            repo_user=request.GET.get('repo_user'),
            repo_name=request.GET.get('repo_name'),
            title=post.title,
            content=post.content)

        form = self.form_class(initial=initial)
        if not settings.GITHUB_ISSUE_OPENING:
            messages.error(request, "GitHub Issue opening is disallowed")
            return render(request, self.template_name, {'form': form})

        # Handle GitHub authorization callback
        if "code" in request.GET and "state" in request.GET and request.GET['state'] is not None:
            if request.user.profile.github_csrf_state != request.GET['state']:
                # Invalid callback
                logger.error("Cross-Site Request Forgery attempt. "
                    "Invalid GitHub authorization callback: {}".format(request.GET))
                return render(request, self.template_name, {'form': form})
            else:
                # Exchange "code" for access token
                api_req_url = 'https://github.com/login/oauth/access_token'
                api_req_data =  {
                        'client_id': settings.GITHUB_APP_CLIENT_ID,
                        'client_secret': settings.GITHUB_APP_CLIENT_SECRET,
                        'code': request.GET['code'],
                        'redirect_uri':
                            settings.CALLBACK_URL_BASE + '/' +
                            'p/github/issue/103/?' +
                            urllib.urlencode({'repo_user': post.github_repo_user, 'repo_name': post.github_repo_name}),
                        'state': request.user.profile.github_csrf_state}

                resp = requests.post(
                    api_req_url + '?' + urllib.urlencode(api_req_data),
                    headers={'Accept': 'application/json'})
                resp_json = resp.json()

                access_token = None
                if 'access_token' in resp_json:
                    access_token = resp_json['access_token']
                    messages.success(request, "GitHub access granted. Now, please click Submit")
                else:
                    logger.error('Failed to get access token from github. '
                        'Response from {} was {}'.format(api_req_url, resp_json))
                    messages.error(request, "Failed to get access token from GitHub")

                # Clear "state" from our DB so it cannot be used again
                request.user.profile.github_csrf_state = None
                request.user.profile.save()

                request.user.profile.github_access_token = access_token
                request.user.profile.save()

        # Check and exit if not a valid edit.
        if not post.is_editable:
            messages.error(request, "This user may not modify the post")
            return HttpResponseRedirect(reverse("home"))

        if not form.is_valid():
            # Invalid form submission.
            return render(request, self.template_name, {'form': form})

        pre = 'class="preformatted"' in post.content
        return render(request, self.template_name, {'form': form, 'pre': pre})

    def post(self, request, *args, **kwargs):

        pk = int(self.kwargs['pk'])
        post = Post.objects.get(pk=pk)
        post = auth.post_permissions(request=request, post=post)

        form = self.form_class(request.POST)

        if not settings.GITHUB_ISSUE_OPENING:
            messages.error(request, "GitHub Issue opening is disallowed")
            return render(request, self.template_name, {'form': form})

        if not form.is_valid():
            # Invalid form submission.
            return render(request, self.template_name, {'form': form})

        post.github_repo_user = request.POST.get('repo_user')
        post.github_repo_name = request.POST.get('repo_name')

        # Get GitHub token
        if request.user.profile.github_access_token is not None:

            # TODO: Do same check on initial GET and display user's profile avatar and name
            # which is in GitHubAPI.check_access_token (see resp_json)
            # see doc https://developer.github.com/v3/oauth_authorizations/#check-an-authorization

            access_token = request.user.profile.github_access_token
            if GitHubAPI.check_access_token(token=access_token):

                issue_body = render(
                    request,
                    self.issue_body_template_name,
                    {
                        'main_body': post.content,
                        'post_url': settings.CALLBACK_URL_BASE + post.get_absolute_url(),
                        'author': post.author },
                    content_type='text/plain')

                # Open GitHub Issue
                issue_number = GitHubAPI.open_issue(
                    access_token=access_token,
                    repo_user=post.github_repo_user,
                    repo_name=post.github_repo_name,
                    issue_title=post.title,
                    issue_body=issue_body.content)

                post.github_issue_number = issue_number
                post.save()

                messages.success(request, "GitHub Issue #{} created".format(issue_number))

                return HttpResponseRedirect(post.get_absolute_url())

        #
        # Redirect user to request GitHub access
        #

        redirect_uri = (
                '{}/p/github/issue/{}/?'.format(settings.CALLBACK_URL_BASE, post.id) +
                urllib.urlencode({'repo_user': post.github_repo_user, 'repo_name': post.github_repo_name}))

        return redirect(GitHubAPI.request_access_token(
            redirect_uri=redirect_uri,
            user_profile=request.user.profile))


    def get_success_url(self):
        return reverse("user_details", kwargs=dict(pk=self.kwargs['pk']))

