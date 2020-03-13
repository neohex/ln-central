from badges.models import Award, AwardDef, Badge
from posts.models import Post, Vote

from django.utils.timezone import utc
from datetime import datetime, timedelta
from common import general_util


def wrap_list(obj, cond):
    return [obj] if cond else []

# Award definitions

# Questions

STUDENT = AwardDef(
    name="Student",
    desc="asked a question earning 1 sat of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=1, author=user, type=Post.QUESTION, is_fake_test_data=False),
    icon="fa fa-certificate"
)

GOOD_QUESTION = AwardDef(
    name="Good Question",
    desc="asked a question earning 5 sats of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=5, author=user, type=Post.QUESTION, is_fake_test_data=False),
    icon="fa fa-question"
)

POPULAR = AwardDef(
    name="Popular",
    desc="asked a question earning 100 sats of up-votes",
    func=lambda user: Post.objects.filter(author=user, view_count__gte=100, is_fake_test_data=False),
    icon="fa fa-eye",
    type=Badge.GOLD,
)

EPIC_QUESTION = AwardDef(
    name="Epic Question",
    desc="created a question earning 10,000 sats of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=10000, author=user, type=Post.QUESTION, is_fake_test_data=False),
    icon="fa fa-bullseye",
    type=Badge.GOLD,
)


# Answers

TEACHER = AwardDef(
    name="Teacher",
    desc="created an answer earning 1 sat of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=1, author=user, type=Post.ANSWER, is_fake_test_data=False),
    icon="fa fa-smile-o"
)

GOOD_ANSWER = AwardDef(
    name="Good Answer",
    desc="created an answer earning 5 sats of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=5, author=user, type=Post.ANSWER, is_fake_test_data=False),
    icon="fa fa-pencil-square-o"
)

SCHOLAR = AwardDef(
    name="Scholar",
    desc="created an answer that has been accepted",
    func=lambda user: Post.objects.filter(author=user, type=Post.ANSWER, has_accepted=True, is_fake_test_data=False),
    icon="fa fa-check-circle-o"
)



# Comments

COMMENTATOR = AwardDef(
    name="Commentator",
    desc="created a comment earning 3 sats of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=3, author=user, type=Post.COMMENT, is_fake_test_data=False),
    icon="fa fa-comment"
)

PUNDIT = AwardDef(
    name="Pundit",
    desc="created a comment earning 10 sats of up-votes",
    func=lambda user: Post.objects.filter(vote_count__gte=10, author=user, type=Post.COMMENT, is_fake_test_data=False),
    icon="fa fa-comments-o",
    type=Badge.SILVER,
)



# Quality

APPRECIATED = AwardDef(
    name="Appreciated",
    desc="created a post earning 5 sats of up-votes",
    func=lambda user: Post.objects.filter(author=user, vote_count__gte=5, is_fake_test_data=False),
    icon="fa fa-heart",
    type=Badge.SILVER,
)


GOLD_STANDARD = AwardDef(
    name="Bitcoin Standard",
    desc="created a post earning 10,000 sats of up-votes",
    func=lambda user: Post.objects.filter(author=user, book_count__gte=10000, is_fake_test_data=False),
    icon="fa fa-music",
    type=Badge.GOLD,
)


# Quantity


CENTURION = AwardDef(
    name="Centurion",
    desc="created 100 posts (questions + answers + comments)",
    func=lambda user: wrap_list(user, Post.objects.filter(author=user, is_fake_test_data=False).count() > 100),
    icon="fa fa-bolt",
    type=Badge.SILVER,
)


ORACLE = AwardDef(
    name="Oracle",
    desc="created 1,000 posts (questions + answers + comments)",
    func=lambda user: wrap_list(user, Post.objects.filter(author=user, is_fake_test_data=False).count() > 1000),
    icon="fa fa-sun-o",
    type=Badge.GOLD,
)

GURU = AwardDef(
    name="Guru",
    desc="created posts that received 100 sats of up-votes total",
    func=lambda user: wrap_list(user, Vote.objects.filter(post__author=user, is_fake_test_data=False).count() > 100),
    icon="fa fa-beer",
    type=Badge.SILVER,
)

PROPHET = AwardDef(
    name="Prophet",
    desc="created posts that received 10,000 sats of up-votes total",
    func=lambda user: wrap_list(user, Vote.objects.filter(post__author=user, is_fake_test_data=False).count() > 10000),
    icon="fa fa-pagelines"
)

MOON = AwardDef(
    name="Moon",
    desc="created posts that received 100,000 sats of up-votes total",
    func=lambda user: wrap_list(user, Vote.objects.filter(post__author=user, is_fake_test_data=False).count() > 100000),
    icon="fa fa-rocket",
    type=Badge.GOLD,
)


def rising_star(user):
    # The user joined no more than three months ago
    cond = general_util.now() < user.profile.date_joined + timedelta(weeks=15)
    cond = cond and Post.objects.filter(author=user, is_fake_test_data=False).count() > 50
    return wrap_list(user, cond)

RISING_STAR = AwardDef(
    name="Rising Star",
    desc="created 50 posts within first three months of joining",
    func=rising_star,
    icon="fa fa-star",
    type=Badge.GOLD,
)

# These awards can only be earned once
ALL_AWARDS = [
    STUDENT,
    GOOD_QUESTION,
    POPULAR,
    EPIC_QUESTION,
    TEACHER,
    GOOD_ANSWER,
    SCHOLAR,
    COMMENTATOR,
    PUNDIT,
    ORACLE,
    CENTURION,
    APPRECIATED,
    GOLD_STANDARD,
    GURU,
    PROPHET,
    MOON,
    RISING_STAR,
]
