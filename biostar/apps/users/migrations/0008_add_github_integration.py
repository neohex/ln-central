# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.add_column(u'users_profile', 'github_csrf_state',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)

        db.add_column(u'users_profile', 'github_access_token',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)

    def backwards(self, orm):
        db.delete_column(u'users_profile', 'github_csrf_state')
        db.delete_column(u'users_profile', 'github_access_token')
