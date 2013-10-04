# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'UserProfile.field'
        db.delete_column('website_userprofile', 'field_id')

        # Deleting field 'UserProfile.facebook_name'
        db.delete_column('website_userprofile', 'facebook_name')

        # Deleting field 'UserProfile.date_of_birth'
        db.delete_column('website_userprofile', 'date_of_birth')

        # Deleting field 'UserProfile.access_token'
        db.delete_column('website_userprofile', 'access_token')

        # Deleting field 'UserProfile.gender'
        db.delete_column('website_userprofile', 'gender')

        # Deleting field 'UserProfile.raw_data'
        db.delete_column('website_userprofile', 'raw_data')


    def backwards(self, orm):
        # Adding field 'UserProfile.field'
        db.add_column('website_userprofile', 'field',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['website.Field'], null=True),
                      keep_default=False)

        # Adding field 'UserProfile.facebook_name'
        db.add_column('website_userprofile', 'facebook_name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.date_of_birth'
        db.add_column('website_userprofile', 'date_of_birth',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.access_token'
        db.add_column('website_userprofile', 'access_token',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.gender'
        db.add_column('website_userprofile', 'gender',
                      self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.raw_data'
        db.add_column('website_userprofile', 'raw_data',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'website.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'website.field': {
            'Meta': {'object_name': 'Field'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'website.hub': {
            'Meta': {'object_name': 'Hub'},
            'is_displayed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'moderator'", 'null': 'True', 'to': "orm['auth.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'primary_key': 'True'})
        },
        'website.hubpermissions': {
            'Meta': {'object_name': 'HubPermissions'},
            'allowed_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'allowed_user'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'hub': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hub'", 'primary_key': 'True', 'to': "orm['website.Hub']"})
        },
        'website.organization': {
            'Meta': {'object_name': 'Organization'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Country']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members_role': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'website.training': {
            'Meta': {'object_name': 'Training'},
            'cowriters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'cowriters'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'creator'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_displayed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.IntegerField', [], {'default': '1327217400'}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'participants'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'resource_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'total_views': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_views_open25': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'website.trainingparticipation': {
            'Meta': {'object_name': 'TrainingParticipation'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'training': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Training']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'website.trainingschedule': {
            'Meta': {'object_name': 'TrainingSchedule'},
            'event_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'training': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Training']"})
        },
        'website.trainingtempshare': {
            'Meta': {'object_name': 'TrainingTempShare'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 2, 17, 0, 0)'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'training': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Training']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'website.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'about_me': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enable_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'facebook_profile_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'isUniStar': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_organization_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_student': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'last_activity_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'linkedin_profile_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Organization']", 'null': 'True'}),
            'twitter_profile_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website_url': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['website']