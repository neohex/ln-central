from __future__ import absolute_import
from django.conf import settings

import logging

from common.log import logger
from users.models import User
from posts.models import Post
from badges.models import Badge, Award
from badges.award_defs import ALL_AWARDS


def init_awards():
    "Initializes the badges"

    for obj in ALL_AWARDS:
        badge, created = Badge.objects.get_or_create(name=obj.name)

        # Badge descriptions may change.
        if badge.desc != obj.desc:
            badge.desc = obj.desc
            badge.icon = obj.icon
            badge.type = obj.type
            badge.save()

        if created:
            logger.info("initializing badge %s" % badge)


# Tries to award a badge to the user
def create_user_award(user):

    logger.info("Award check for %s" % user.id)

    # Update user status.
    if (user.status == User.NEW_USER) and (user.score > 10):
        user.status = User.TRUSTED
        user.save()

    # Debug only
    #Award.objects.all().delete()


    Award.objects.filter(user=user)

    # The awards the user has won at this point
    awards = dict()
    for award in Award.objects.filter(user=user).select_related('badge'):
        awards.setdefault(award.badge.name, []).append(award)

    # Shorcut function to get the award count
    get_award_count = lambda name: len(awards[name]) if name in awards else 0

    for obj in ALL_AWARDS:

        # How many times has been awarded
        seen_count = get_award_count(obj.name)

        # How many times should it been awarded
        valid_targets = obj.validate(user)

        # Keep that targets that have not been awarded
        valid_targets = valid_targets[seen_count:]

        # Some limit on awards
        valid_targets = valid_targets[:100]

        # Award the targets
        for target in valid_targets:
            # Update the badge counts.
            badge = Badge.objects.get(name=obj.name)

            date = user.profile.last_login
            award, created = Award.objects.get_or_create(user=user, badge=badge, date=date, context="")
            if created:
                badge.count += 1
                badge.save()
                logger.info("award %s created for %s" % (award.badge.name, user.pubkey))
