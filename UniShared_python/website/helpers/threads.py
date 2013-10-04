#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 14 sept. 2012

@author: Arnaud
'''
from threading import Thread
from urllib import urlencode
from urllib2 import urlopen
import random
import time

from django.conf import settings
from django.db.models.query_utils import Q
from django.template import Context
from django_facebook.api import get_facebook_graph
from open_facebook.exceptions import OpenFacebookException, PermissionException, \
    OAuthException
from social_auth.backends.facebook import ACCESS_TOKEN
from social_auth.db.django_models import UserSocialAuth

from UniShared_python.website.helpers.helpers import LoggingHelper, SessionHelper
from UniShared_python.website.models import TrainingTempShare, TrainingParticipation
from UniShared_python.website.tasks import email_task
from UniShared_python.website.helpers.helpers import ProfileHelper, GoogleDriveHelper
from UniShared_python.website.models import Training


class FacebookThread(Thread):
    def __init__(self, user, facebook_id, action, params):
        Thread.__init__(self)
        
        self.action = action
        self.params = params
        self.facebook_id = facebook_id
        self.user = user
    
    def run(self):
        try:
            access_token = UserSocialAuth.objects.get(user=self.user, provider='facebook').extra_data['access_token']
            self.graph = get_facebook_graph(access_token=access_token)
            if self.graph:
                for n in range(0, 5):
                    try:
                        url = None
                        try:
                            if u'class' in self.params:
                                url = self.params[u'class']
                            elif u'link' in self.params:
                                url = self.params[u'link']
                            if url:
                                self.graph.set(u'/', {'ids' : url, 'scrape' : 'true'})
                        except OAuthException:
                            LoggingHelper.getDebugLogger().debug(u'Error while scraping {0}'.format(url), exc_info=1)

                        return self.graph.set(u'{0}/{1}'.format(self.facebook_id, self.action), self.params)
                    except PermissionException:
                        LoggingHelper.getDebugLogger().debug(u'Permission not granted (facebook_id : {0}, action {1}, params {2})'.format(self.facebook_id, self.action, self.params), exc_info=1)
                    except OAuthException:
                        LoggingHelper.getDebugLogger().debug(u'Refreshing token (facebook_id : {0}, action {1}, params {2})'.format(self.facebook_id, self.action, self.params), exc_info=1)
                        self.refresh_token()
                    except OpenFacebookException:
                        LoggingHelper.getErrorLogger().error(u'Error while posting on Facebook (facebook_id : {0}, action {1}, params {2})'.format(self.facebook_id, self.action, self.params), exc_info=1)
                        time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        except UserSocialAuth.DoesNotExist:
            LoggingHelper.getDebugLogger().debug('No access token')
                    
    def refresh_token(self):
        user_social_auth = UserSocialAuth.objects.get(user=self.user, provider='facebook')
        
        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'grant_type': 'fb_exchange_token',
            'client_secret': settings.FACEBOOK_API_SECRET,
            'fb_exchange_token': user_social_auth.extra_data['access_token']
        }

        try:
            response = urlopen(ACCESS_TOKEN + urlencode(params)).read()
            # Keys in response are: access_token, expires
            response_dict = dict((k, v) for k, v in (e.split('=') for e in response.split('&')))
            user_social_auth.extra_data['access_token'] = response_dict['access_token']
            user_social_auth.extra_data['expires'] = response_dict['expires']
            user_social_auth.save()
        except (ValueError, KeyError):
            # Error at response['error'] with possible description at
            # response['error_description']
            LoggingHelper.getErrorLogger().error(u'Error while refreshing access token on Facebook (error : {0}, description : {1})'.format(response['error'], response['error_description']), exc_info=1)
            
                    
class FacebookActionThread(FacebookThread):
    def __init__(self, user, facebook_id, action, params):
        FacebookThread.__init__(self, user, facebook_id, '{0}:{1}'.format(settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, action), params)
        
class FacebookEventThread(FacebookThread):
    def __init__(self, user, facebook_id, session_key, name, start_time, location, invited, privacy_type='OPEN'):
        FacebookThread.__init__(self, user, facebook_id, 'events', {'name':name, 'start_time':start_time,'location':location,'privacy_type':privacy_type})
        self.invited = invited
        self.user = user
        self.session_key = session_key
    
    def run(self):
        event_id = FacebookThread.run(self)
        
        if event_id and 'id' in event_id and self.invited:
            if self.session_key:
                SessionHelper.put_key_value_in_session(self.session_key, event_id=event_id['id'])
            FacebookEventInviteThread(self.user, event_id['id'], self.invited).start()
            
        return event_id
        
class FacebookEventInviteThread(FacebookThread):
    def __init__(self, user, event_id, users):
        FacebookThread.__init__(self, user, event_id, 'invited', {'users':users})  
            
class TrainingTempShareThread(Thread):
    def __init__(self, training, user):
        Thread.__init__(self)
        
        self.user = user
        self.training = training
        
    def run(self):
        logger = LoggingHelper.getDebugLogger()
        logger.debug('Looking for a temporary share for training {0} and user {1}'.format(self.training.resource_id, self.user))
        
        trainingShare = TrainingTempShare.objects.filter(Q(facebook_id=self.user.get_profile().facebook_id) | Q(email=self.user.email), training=self.training)
        if trainingShare.exists():
            logger.debug('Temporary share found for training {0} and user {1}'.format(self.training.resource_id, self.user))
            if self.training.creator != self.user and self.user not in self.training.cowriters.all():     
                logger.debug('Adding co-writer for training {0} and user {1}'.format(self.training.resource_id, self.user))
                self.training.cowriters.add(self.user) 
                
                if self.user in self.training.participants.all():
                    logger.debug('Remove participant for training {0} and user {1}'.format(self.training.resource_id, self.user))
                    self.training.participants.remove(self.user)
                
            trainingShare.delete()
        elif self.training.creator != self.user and self.user not in self.training.cowriters.all() and self.user not in self.training.participants.all():
            logger.debug('Adding participant for training {0} and user {1}'.format(self.training.resource_id, self.user))
            self.training.participants.add(self.user)

            if Training.objects.filter(participants=self.user).count() == 1:
                logger.debug('Sending first participation mail')
                context = Context({'username': self.user.username, 'first_name' : self.user.first_name, 'profile_url' : ProfileHelper.get_profile_url(self.user.username), 'document_url' : GoogleDriveHelper.get_document_url(self.training.resource_id), 'document_title' : self.training.title, 'ga_campaign_params' : 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=new_document_participation_mail'})
                email_task.apply_async(["Yihaa, you participated in a collaborative document!", context, "new_document_participation_mail", [self.user.email]])
        
        try:
            logger.debug('Adding participation for training {0} and user {1}'.format(self.training.resource_id, self.user))
            participation = TrainingParticipation.objects.get(user=self.user, training=self.training)
            participation.count += 1
            participation.save()
        except TrainingParticipation.DoesNotExist:
            TrainingParticipation.objects.create(user=self.user, training=self.training, count=1)