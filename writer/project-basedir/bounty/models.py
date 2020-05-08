from django.db import models
from django.utils import timezone

from django.apps import apps

try:
    # writer
    from posts.models import Post
except ImportError:
    # reader
    from biostar.apps.posts.models import Post


class CustomModel(models.Model):
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(CustomModel, self).save(*args, **kwargs)

class Bounty(CustomModel):
    post_id = models.ForeignKey(
        to=Post,
        verbose_name='post_id of the Question where the bounty is posted',
        on_delete=models.CASCADE
    )

    amt = models.IntegerField(
        verbose_name='amount in sats of the total award for winning the bounty',
        default=-1
    )

    is_active = models.BooleanField(
        verbose_name="is_active, false if the Bounty still can be awarded",
        default=True
    )

    is_payed = models.BooleanField(
        verbose_name="is_payed, true when the winner took custody of the funds",
        default=False
    )

    activation_time = models.DateTimeField(
        verbose_name="activation_time is when the bounty became active most recently",
    )

    award_time = models.DateTimeField(
        verbose_name="award_time is when the winner was announced",
        null=True,
        blank=True,
    )


class BountyAward(CustomModel):
    bounty_id = models.ForeignKey(
        to=Bounty,
        verbose_name="bounty_id which bounty is awarded",
        on_delete=models.CASCADE
    )

    post_id = models.ForeignKey(
        to=Post,
        verbose_name="post_id which Answer post won the awarded",
        on_delete=models.CASCADE
    )
