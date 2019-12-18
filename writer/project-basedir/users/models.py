from __future__ import print_function, unicode_literals, absolute_import, division
import logging
from django import forms
from django.db import models
from django.conf import settings
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.timezone import utc

from common import const
from common import general_util
from common import html_util
from common import json_util

import bleach
# TODO: remove version check after upgrading reader 
import django
if django.VERSION[0] == 1:
    from django.core.urlresolvers import reverse
else:
    from django.urls import reverse
from django.contrib.sites.models import Site
from datetime import datetime, timedelta


# HTML sanitization parameters.
ALLOWED_TAGS = bleach.ALLOWED_TAGS + settings.ALLOWED_TAGS
ALLOWED_STYLES = bleach.ALLOWED_STYLES + settings.ALLOWED_STYLES
ALLOWED_ATTRIBUTES = dict(bleach.ALLOWED_ATTRIBUTES)
ALLOWED_ATTRIBUTES.update(settings.ALLOWED_ATTRIBUTES)

logger = logging.getLogger(__name__)


class LocalManager(models.Manager):
    def get_users(self, sort, limit, q):
        sort = const.USER_SORT_MAP.get(sort, None)
        days = const.POST_LIMIT_MAP.get(limit, 0)

        if q:
            query = self.filter(name__icontains=q)
        else:
            query = self

        if days:
            delta = general_util.now() - timedelta(days=days)
            query = self.filter(profile__last_login__gt=delta)


        query = query.exclude(status=User.BANNED).select_related("profile").order_by(sort)

        return query


class User(models.Model):
    # Class level constants.
    USER, MODERATOR, ADMIN, BLOG = range(4)
    TYPE_CHOICES = [(USER, "User"), (MODERATOR, "Moderator"), (ADMIN, "Admin"), (BLOG, "Blog")]

    NEW_USER, TRUSTED, SUSPENDED, BANNED = range(4)
    STATUS_CHOICES = ((NEW_USER, 'New User'), (TRUSTED, 'Trusted'), (SUSPENDED, 'Suspended'), (BANNED, 'Banned'))

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'pubkey'
    objects = LocalManager()

    # Default information on every user.
    pubkey = models.CharField(verbose_name='LN Identity PubKey', db_index=True, max_length=255, unique=True)

    # This designates a user types and with that permissions.
    type = models.IntegerField(choices=TYPE_CHOICES, default=USER)

    # This designates a user statuses on whether they are allowed to log in.
    status = models.IntegerField(choices=STATUS_CHOICES, default=NEW_USER)

    # The number of new messages for the user.
    new_messages = models.IntegerField(default=0)

    # The number of badges for the user.
    badges = models.IntegerField(default=0)

    # Activity score computed over a shorter period.
    score = models.IntegerField(default=0)

    # User's recent activity level.
    activity = models.IntegerField(default=0)

    # Display next to a user name.
    flair = models.CharField(verbose_name='Flair', max_length=15, default="")

    # The site this users belongs to.
    site = models.ForeignKey(Site, null=True, on_delete=models.CASCADE)

    # The last visit by the user.
    last_login = models.DateTimeField()

    # Rows used for testing
    is_fake_test_data = models.BooleanField(default=False)

    @property
    def is_moderator(self):
        return self.type == User.MODERATOR or self.type == User.ADMIN

    @property
    def is_administrator(self):
        return self.type == User.ADMIN

    @property
    def is_trusted(self):
        return self.status == User.TRUSTED

    @property
    def is_suspended(self):
        return self.status == User.SUSPENDED or self.status == User.BANNED

    def get_full_name(self):
        # The user is identified by their pubkey address
        return self.pubkey

    def get_short_name(self):
        # The user is identified by their pubkey address
        return self.pubkey

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def save(self, *args, **kwargs):
        "Actions that need to be performed on every user save."

        super(User, self).save(*args, **kwargs)

    @property
    def scaled_score(self):
        "People like to see big scores."
        return self.score * 10

    def __unicode__(self):
        return "%s (id=%s, last_login: %s)" % (self.pubkey, self.id, self.last_login)

    def get_absolute_url(self):
        url = reverse("user-details", kwargs=dict(pk=self.id))
        return url


class Tag(models.Model):
    name = models.TextField(max_length=50, db_index=True)
    is_fake_test_data = models.BooleanField(default=False)


class Profile(models.Model):
    """
    Maintains information that does not always need to be retreived whe a user is accessed.
    """
    LOCAL_MESSAGE, EMAIL_MESSAGE = const.LOCAL_MESSAGE, const.EMAIL_MESSAGE
    NO_DIGEST, DAILY_DIGEST, WEEKLY_DIGEST, MONTHLY_DIGEST = range(4)
    TYPE_CHOICES = const.MESSAGING_TYPE_CHOICES

    DIGEST_CHOICES = [(NO_DIGEST, 'Never'), (DAILY_DIGEST, 'Daily'),
                      (WEEKLY_DIGEST, 'Weekly'), (MONTHLY_DIGEST, 'Monthly')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Globally unique id used to identify the user in a private feeds
    uuid = models.CharField(null=False, db_index=True, unique=True, max_length=255)

    # The last visit by the user.
    last_login = models.DateTimeField()

    # The last visit by the user.
    date_joined = models.DateTimeField()

    # User provided website.
    website = models.URLField(default="", max_length=255, blank=True)

    # This field is used to select content for the user.
    my_tags = models.TextField(default="", max_length=255, blank=True)

    # Description provided by the user html.
    info = models.TextField(default="", null=True, blank=True)

    # The default notification preferences.
    message_prefs = models.IntegerField(choices=TYPE_CHOICES, default=const.LOCAL_MESSAGE)

    # This stores binary flags on users. Their usage is to
    # allow easy subselection of various subsets of users.
    flag = models.IntegerField(default=0)

    # The tag value is the canonical form of the post's tags
    watched_tags = models.CharField(max_length=100, default="", blank=True)

    # The tag set is built from the watch_tag string and is used to trigger actions
    # when a post that matches this tag is set
    tags = models.ManyToManyField(Tag, blank=True, )

    # Subscription to daily and weekly digests.
    digest_prefs = models.IntegerField(choices=DIGEST_CHOICES, default=WEEKLY_DIGEST)

    # Opt-in to all messages from the site
    opt_in = models.BooleanField(default=False)

    is_fake_test_data = models.BooleanField(default=False)

    def parse_tags(self):
        return html_util.split_tags(self.tag_val)

    def clear_data(self):
        "Actions to take when suspending or banning users"
        self.website = self.info = ''
        self.save()

    def add_tags(self, text):
        text = text.strip()
        # Sanitize the tag value
        self.tag_val = bleach.clean(text, tags=[], attributes=[], styles={}, strip=True)
        # Clear old tags
        self.tags.clear()
        tags = [Tag.objects.get_or_create(name=name)[0] for name in self.parse_tags()]
        self.tags.add(*tags)

    def save(self, *args, **kwargs):

        # Clean the info fields.
        self.info = bleach.clean(self.info, tags=ALLOWED_TAGS,
                                 attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)

        if not self.id:
            # This runs only once upon object creation.
            self.uuid = general_util.make_uuid()
            self.date_joined = self.date_joined or general_util.now()
            self.last_login = self.date_joined

        super(Profile, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % self.user.pubkey

    @property
    def filled(self):
        has_info = bool(self.info.strip())
        return has_info

    @staticmethod
    def auto_create(sender, instance, created, *args, **kwargs):
        "Should run on every user creation."
        if created:
            prof = Profile(user=instance)
            prof.save()


class UserChangeForm(forms.ModelForm):
    """A form for updating users."""

    class Meta:
        model = User
        fields = ['type']


# Data signals
from django.db.models.signals import post_save

post_save.connect(Profile.auto_create, sender=User)