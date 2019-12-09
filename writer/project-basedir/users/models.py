from django.db import models
from django.contrib.sites.models import Site
from datetime import datetime
from common import const


def now():
    return datetime.utcnow().replace(tzinfo=utc)


class User(models.Model):
    # Class level constants.
    USER, MODERATOR, ADMIN, BLOG = range(4)
    TYPE_CHOICES = [(USER, "User"), (MODERATOR, "Moderator"), (ADMIN, "Admin"), (BLOG, "Blog")]

    NEW_USER, TRUSTED, SUSPENDED, BANNED = range(4)
    STATUS_CHOICES = ((NEW_USER, 'New User'), (TRUSTED, 'Trusted'), (SUSPENDED, 'Suspended'), (BANNED, 'Banned'))

    # Default information on every user.
    pubkey = models.CharField(verbose_name='LN Identity Pubkey', db_index=True, max_length=255, unique=True)

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
    last_login = models.DateTimeField(default=datetime.now)


class Tag(models.Model):
    name = models.TextField(max_length=50, db_index=True)


class Profile(models.Model):
    """
    Maintains information that does not always need to be retreived whe a user is accessed.
    """
    LOCAL_MESSAGE, EMAIL_MESSAGE = const.LOCAL_MESSAGE, const.EMAIL_MESSAGE
    NO_DIGEST, DAILY_DIGEST, WEEKLY_DIGEST, MONTHLY_DIGEST = range(4)
    TYPE_CHOICES = const.MESSAGING_TYPE_CHOICES

    DIGEST_CHOICES = [(NO_DIGEST, 'Never'), (DAILY_DIGEST, 'Daily'),
                      (WEEKLY_DIGEST, 'Weekly'), (MONTHLY_DIGEST, 'Monthly')]
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)

    # Globally unique id used to identify the user in a private feeds
    uuid = models.CharField(null=False, db_index=True, unique=True, max_length=255)

    # The last visit by the user.
    last_login = models.DateTimeField()

    # The last visit by the user.
    date_joined = models.DateTimeField()

    # User provided location.
    location = models.CharField(default="", max_length=255, blank=True)

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

    def parse_tags(self):
        return util.split_tags(self.tag_val)

    def clear_data(self):
        "Actions to take when suspending or banning users"
        self.website = self.info = self.location = ''
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

        # Strip whitespace from location string
        self.location = self.location.strip()

        if not self.id:
            # This runs only once upon object creation.
            self.uuid = util.make_uuid()
            self.date_joined = self.date_joined or now()
            self.last_login = self.date_joined

        super(Profile, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % self.user.pubkey

    @property
    def filled(self):
        has_location = bool(self.location.strip())
        has_info = bool(self.info.strip())
        return has_location and has_info

    @staticmethod
    def auto_create(sender, instance, created, *args, **kwargs):
        "Should run on every user creation."
        if created:
            prof = Profile(user=instance)
            prof.save()
