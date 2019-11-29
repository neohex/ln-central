# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'EmailList'
        db.delete_table(u'users_emaillist')

        # Deleting field 'Profile.location'
        db.delete_column(u'users_profile', 'location')

        # Adding unique constraint on 'User', fields ['pubkey']
        db.create_unique(u'users_user', ['pubkey'])


    def backwards(self, orm):
        # Removing unique constraint on 'User', fields ['pubkey']
        db.delete_unique(u'users_user', ['pubkey'])

        # Adding model 'EmailList'
        db.create_table(u'users_emaillist', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=255, unique=True, db_index=True)),
        ))
        db.send_create_signal(u'users', ['EmailList'])

        # Adding field 'Profile.location'
        db.add_column(u'users_profile', 'location',
                      self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True),
                      keep_default=False)


    models = {
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'users.profile': {
            'Meta': {'object_name': 'Profile'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {}),
            'digest_prefs': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'flag': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'default': "u''", 'null': 'True', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {}),
            'message_prefs': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'my_tags': ('django.db.models.fields.TextField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'opt_in': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['users.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['users.User']", 'unique': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'watched_tags': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'})
        },
        u'users.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'max_length': '50', 'db_index': 'True'})
        },
        u'users.user': {
            'Meta': {'object_name': 'User'},
            'activity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'badges': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'flair': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '15'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {}),
            'new_messages': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pubkey': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['users']