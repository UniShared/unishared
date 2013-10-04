#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
from datetime import datetime
import operator

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.db import models as django_models
from django.db.models.signals import post_save
from django.dispatch import receiver
from batch_select.models import BatchManager
from oauth2client.django_orm import CredentialsField
from south.modelsinspector import add_introspection_rules


class CredentialsModel(django_models.Model):
    id = django_models.ForeignKey(User, primary_key=True)
    credential = CredentialsField()

add_introspection_rules([], ["^oauth2client\.django_orm\.CredentialsField"])
add_introspection_rules([], ["^oauth2client\.django_orm\.FlowField"])

# Country Model
class Country(django_models.Model):
    name= django_models.CharField(max_length=20)

# Organization model
class Organization(django_models.Model):
    name = django_models.CharField(max_length=100)
    country = django_models.ForeignKey(Country, null=True)
    members_role = django_models.CharField(max_length=30)
    
    def natural_key(self):
        return (self.name,)

    def natural_key(self):
        return (self.name,)

# Field model
class Field(django_models.Model):
    name = django_models.CharField(max_length=50)
    
# Training model    
class Training(django_models.Model):
    type = django_models.CharField(max_length=30)
    resource_id = django_models.CharField(max_length=100, db_index=True)
    is_live = django_models.BooleanField()
    is_displayed = django_models.BooleanField()
    is_featured = django_models.BooleanField()
    is_deleted = django_models.BooleanField()
    last_updated = django_models.IntegerField(default=1327217400)
    title = django_models.CharField(max_length=256, db_index=True)
    creator = django_models.ForeignKey(User, related_name='creator')
    cowriters = django_models.ManyToManyField(User, related_name='cowriters')
    participants = django_models.ManyToManyField(User, related_name='participants')
    total_views = django_models.IntegerField(default=0)
    total_views_open25 = django_models.IntegerField(default=0)

    objects = BatchManager()
  
# Model used to store cowriters after creating a class
class TrainingTempShare(django_models.Model):
    training = django_models.ForeignKey(Training)

    user_who_invites = django_models.ForeignKey(User, null=True, related_name='user_who_invites')
    user_invited = django_models.ForeignKey(User, null=True, related_name='user_invited')

    facebook_id = django_models.BigIntegerField(null=True)
    email = django_models.EmailField(null=True)

    role = django_models.CharField(max_length=12, choices=(('cowriters', 'cowriters'), ('participants', 'participants')))
    last_updated = django_models.DateTimeField(default=datetime.now())
    
# Training model to store training schedule
class TrainingSchedule(django_models.Model):
    training = django_models.ForeignKey(Training)
    start_time = django_models.DateTimeField()
    event_id = django_models.BigIntegerField(null=True)
    
class TrainingParticipation(django_models.Model):
    training = django_models.ForeignKey(Training)
    user = django_models.ForeignKey(User)
    count = django_models.IntegerField()

User.email = django_models.EmailField(_('e-mail address'), blank=True, max_length=200)
    
# User profile model
class UserProfile(django_models.Model):
    user = django_models.ForeignKey(User, unique=True)
    
    organization = django_models.ForeignKey(Organization, null=True)
    is_organization_verified=django_models.BooleanField(default=True)
    isUniStar = django_models.BooleanField()
    is_student = django_models.NullBooleanField(default=True)
    is_email_verified = django_models.BooleanField()
    enable_notifications = django_models.BooleanField()
    about_me = django_models.TextField(blank=True)
    facebook_id = django_models.BigIntegerField(blank=True, unique=True, null=True)
    facebook_profile_url = django_models.TextField(blank=True)
    twitter_profile_url = django_models.TextField(blank=True)
    linkedin_profile_url = django_models.TextField(blank=True)
    website_url = django_models.TextField(blank=True)
    image = django_models.ImageField(upload_to='profile_images')
    last_seen = django_models.DateTimeField(null=True)
    last_activity_ip = django_models.IPAddressField(null=True)
    drive_folder_id = django_models.CharField(max_length=250, null=True)
    can_create = django_models.BooleanField(default=False)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, raw, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if created and not raw:
        UserProfile.objects.get_or_create(user=instance)

"""
class StatDocument(django_models.Model):
    resource = django_models.ForeignKey(Training)
    hits = django_models.IntegerField()
"""

class Hub(django_models.Model):
    user = django_models.ForeignKey(User, primary_key=True)
    moderator = django_models.ForeignKey(User, null=True, related_name='moderator')

    is_featured = django_models.BooleanField(default=False)
    is_displayed = django_models.BooleanField(default=False)
    is_live = django_models.BooleanField(default=False)

    @staticmethod
    def search(query, **kwargs):
        keywords = query.split(',')
        list_title_qs = [Q(user__username__icontains=keyword) for keyword in keywords]
        final_q = reduce(operator.or_, list_title_qs)
        return Hub.objects.filter(final_q, is_displayed=True, user__is_active=True).select_related('user')


class HubPermissions(django_models.Model):
    hub = django_models.ForeignKey(Hub, primary_key=True, related_name='hub')
    allowed_user = django_models.ForeignKey(User, unique=True, related_name='allowed_user')

# Note taking buddies related models
class NoteTakingBuddy(django_models.Model):
    class Meta:
        unique_together = ("hub", "user")

    hub = django_models.ForeignKey(Hub)
    user = django_models.ForeignKey(User)

    # Note taking formats
    BULLET_POINTS = "BULLET_POINTS"
    FULL_SENTENCES = "FULL_SENTENCES"
    IMAGES = "IMAGES"
    SCREENSHOTS_COURSE_VIDEO = "SCREENSHOTS_COURSE_VIDEO"
    COMMENTS_DISCUSSION_THREADS = "COMMENTS_DISCUSSION_THREADS"
    LINKS_WEB_RESSOURCES = "LINKS_WEB_RESSOURCES"
    CHATING = "CHATING"
    REVISION_PLANNING = "REVISION_PLANNING"
    NOTE_TAKING_FORMAT_CHOICES = (
        (BULLET_POINTS, "Bullet points"),
        (FULL_SENTENCES, "Full sentences"),
    )
    note_taking_format = django_models.CharField(max_length=30, choices=NOTE_TAKING_FORMAT_CHOICES)
    passionated_by_subject = django_models.BooleanField()
    augmented_documents = django_models.BooleanField()

    # Behaviours
    WRITE_MOST_NOTES = "WRITE_MOST_NOTES"
    IMPROVE_EXISTING_NOTES = "IMPROVE_EXISTING_NOTES"
    READ_NOTES = "READ_NOTES"
    BEHAVIOR_CHOICES = (
        (WRITE_MOST_NOTES, "Write most of the notes"),
        (IMPROVE_EXISTING_NOTES, "Improve existing notes"),
        (READ_NOTES, "Read them")
    )
    behavior = django_models.CharField(max_length=22, choices=BEHAVIOR_CHOICES)
    live_session = django_models.BooleanField()
    score = django_models.IntegerField()

    def get_score(self):
        return int(self.note_taking_format == NoteTakingBuddy.FULL_SENTENCES) + int(self.augmented_documents) + int(self.live_session) # Between 0 and 3