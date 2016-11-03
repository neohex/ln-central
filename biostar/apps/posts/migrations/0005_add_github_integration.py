# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.add_column(u'posts_post', 'github_repo_user',
                      self.gf('django.db.models.fields.TextField')(default=u''),
                      keep_default=False)

        db.add_column(u'posts_post', 'github_repo_name',
                      self.gf('django.db.models.fields.TextField')(default=u''),
                      keep_default=False)

        db.add_column(u'posts_post', 'github_issue_number',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

    def backwards(self, orm):
        db.delete_column(u'posts_post', 'github_repo_user')
        db.delete_column(u'posts_post', 'github_repo_name')
        db.delete_column(u'posts_post', 'github_issue_number')
