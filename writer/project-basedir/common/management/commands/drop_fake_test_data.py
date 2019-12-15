import pprint

from django.core.management.base import BaseCommand, CommandError

from users.models import User
from posts.models import Post
from badges.models import Badge

class Command(BaseCommand):
    help = 'Drops fake test data'

    def handle(self, *args, **options):
        delete_summary = {}

        tables = []
        tables += [User.objects.filter(is_fake_test_data=True)]
        tables += [Post.objects.filter(is_fake_test_data=True)]
        tables += [Badge.objects.filter(is_fake_test_data=True)]

        for t in tables:
            stats = t.delete()
            for key, num_deleted in stats[1].items():
                delete_summary[key] = num_deleted

        self.stdout.write(self.style.SUCCESS("Successfully dropped rows"))
        self.stdout.write(pprint.pformat(delete_summary))
