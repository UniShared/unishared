#!/usr/bin/python
# -*- coding: utf-8 -*-
import multiprocessing
from collections import Iterable
import operator

from apiclient import errors
from apiclient.discovery import build
from apiclient.http import BatchHttpRequest
from django.core.urlresolvers import reverse
import httplib2
from oauth2client.django_orm import Storage


__author__ = 'Arnaud'

import logging
import random
import time

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from sorl.thumbnail import get_thumbnail
import dns.resolver
import re

from UniShared_python.website.models import Training, UserProfile, Organization, CredentialsModel

class GoogleDriveHelper:
    __clientInstance = None

    DOCUMENTS_LIST_API_BATCH_URL = 'https://docs.google.com/feeds/default/private/full/batch'
    DOCUMENT_LIST_API_ITEM_TEMPLATE = 'https://docs.google.com/feeds/id/%s'
    RESOURCE_ID_REGEX = re.compile(DOCUMENT_LIST_API_ITEM_TEMPLATE % "document:([a-z0-9_-]+)", re.IGNORECASE)

    TITLE_FILTER = ['your new unishared\'s class', 'document title', 'untitled document', 'test', 'copy of template', 'unishared template', 'template']

    MAX_DOCUMENTS = 50

    @staticmethod
    def get_docs_client():
        """
        Return the unique instance of the Docs client
        """
        if GoogleDriveHelper.__clientInstance is None:
            user = User.objects.get(username='arnaud.breton')
            storage = Storage(CredentialsModel, 'id', user, 'credential')
            credential = storage.get()

            http = httplib2.Http()
            http = credential.authorize(http)
            GoogleDriveHelper.__clientInstance = build("drive", "v2", http=http)

        return GoogleDriveHelper.__clientInstance

    @staticmethod
    def _get_unistar_collection_name(username):
        """ Return the name for a UniStar GDocs collection
        Args:
        username : UniStars's username
        """
        return '[UniShared-{0}] {1}'.format(settings.ENV_NAME, username)
        
    @staticmethod
    def get_document_url(resource_id):
        return '{0}{1}'.format(settings.BASE_URL, reverse('website.views.embedded_document', args=[resource_id]))

    @staticmethod
    def search_documents(query, **kwargs):
        logger = LoggingHelper.getDebugLogger()

        title_only = kwargs.get('title_only', False)

        keywords = [keyword for keyword in query.split(',')]

        list_title_qs = [Q(title__icontains=keyword) for keyword in keywords]
        final_q = reduce(operator.or_, list_title_qs)
        documents = Training.objects.filter(final_q).values_list('resource_id', flat=True)

        if title_only:
            return documents
        else:
            #max_results = kwargs.get('max_results', GoogleDriveHelper.MAX_DOCUMENTS)
            #max_results_criteria = 'maxResults='+str(max_results)
            parents_critera = "not '{0}' in parents".format(settings.DRIVE_TRASHBIN_FOLDER_ID)
            full_text_criteria = ' or '.join([u"fullText contains '{0}'".format(keyword.lower()) for keyword in keywords ])
            trashed_criteria = 'trashed=false'
            drive_query = ' and '.join([full_text_criteria, parents_critera, trashed_criteria])

            drive_results_ids = []
            try:
                logger.debug(u'Drive query {0}'.format(drive_query))
                client = GoogleDriveHelper.get_docs_client()
                params = {'q': drive_query}
                drive_results = client.files().list(**params).execute()['items']
                drive_results_ids.extend([item['id'] for item in drive_results])
            except errors.HttpError:
                logger.error('Error while calling Drive API')

            return list(set(list(documents) + drive_results_ids))

    @staticmethod
    def get_all_user_documents(user, **kwargs):
        """
        Return all the documents for a user

        Args :
        user : the user to fetch documents. If none, the method fetch all the documents.
        for_user: the user who is consulting the user's documents.
        For a user, it fetches all his documents (created and cowrited).
        For a hub, it fetches all the documents where it's cowriter.
        """
        logger = LoggingHelper.getDebugLogger()
        query = kwargs.get('query', None)

        if user:
            """
            if user.get_profile().isUniStar:
                logger.debug(u'Fetching all the documents of {0} (UniStar)'.format(user.username))
                
                # Documents where the user is creator, cowriter or participant
                documents = Training.objects.order_by('-last_updated').batch_select('cowriters', 'participants').filter(Q(creator=user) | Q(cowriters = user) | Q(participants=user), is_deleted=False).distinct()
            else:
                logger.debug(u'Fetching all the documents of {0} (Hub)'.format(user.username))

                # Documents where user is cowriter or creator
            """
            logger.debug(u'Fetching all the documents of {0}'.format(user.username))

            documents = Training.objects.batch_select('cowriters','participants').order_by('-last_updated').filter(Q(creator=user) | Q(cowriters = user) | Q(participants=user), is_deleted=False)

            if query:
                results = GoogleDriveHelper.search_documents(query, title_only=kwargs.get('title_only', False))
                documents = documents.filter(resource_id__in=results)

            documents = documents.distinct()

            max_documents = kwargs.get('max_documents', GoogleDriveHelper.MAX_DOCUMENTS)
            id_page = kwargs.get('id_page', 1)
            return len(documents), GoogleDriveHelper.get_documents(documents, max_documents=max_documents, id_page=id_page)
        else:
            return []
    
    @staticmethod
    def get_all_documents(**kwargs):
        """
        GET all documents
        """
        logger = LoggingHelper.getDebugLogger()

        live_only = kwargs.get('live_only', False)
        featured_only = kwargs.get('featured_only', False)
        query = kwargs.get('query', None)
        title_only = kwargs.get('title_only', False)

        if live_only:
            documents = Training.objects.batch_select('cowriters','participants').filter(is_live=True, is_displayed=True, is_deleted=False).order_by('-last_updated')
        elif featured_only:
            documents = Training.objects.batch_select('cowriters','participants').filter(is_featured=True, is_displayed=True, is_deleted=False).order_by('-last_updated')
        elif query:
            results = GoogleDriveHelper.search_documents(query, title_only=title_only)
            documents = Training.objects.batch_select('cowriters','participants').filter(resource_id__in=results, is_displayed=True, is_deleted=False).order_by('-last_updated')
        else:
            documents = Training.objects.batch_select('cowriters','participants').filter(is_displayed=True, is_deleted=False).order_by('-last_updated')

        documents = documents.distinct()
        max_documents = kwargs.get('max_documents', GoogleDriveHelper.MAX_DOCUMENTS)
        id_page = kwargs.get('id_page', 1)
        return len(documents), GoogleDriveHelper.get_documents(documents, max_documents=max_documents, id_page=id_page)

    @staticmethod
    def get_documents(documents, **kwargs):
        """
        Retrieve documents, paginated

        Args:
        user: The user who is consulting the documents
        documents: The documents to retrieve
        """
        if documents and len(documents):
            max_documents = kwargs.get('max_documents', GoogleDriveHelper.MAX_DOCUMENTS)
            if max_documents > GoogleDriveHelper.MAX_DOCUMENTS:
                max_documents = GoogleDriveHelper.MAX_DOCUMENTS

            paginator = Paginator(documents, max_documents)

            try:
                id_page = kwargs.get('id_page', 1)
                page = paginator.page(id_page)
            except (EmptyPage, InvalidPage):
                page = paginator.page(1)

            return page.object_list
        else:
            return []

    @staticmethod
    def _query_resources_batch(resources_ids):
        """
        Retrieving all resources via a batch query
        
        Args:
        resources_ids: IDs' to retrieve
        """
        logger = LoggingHelper.getDebugLogger()
        
        client = GoogleDriveHelper.get_docs_client()
        if isinstance(resources_ids, str):
            logger.debug(u'Just one resource to query, calling without batch')
            for n in range(0, 5):
                try:
                    return client.files.get(fileId=resources_ids).execute()
                except errors.HttpError, error:
                    if error.status == 404:
                        document_to_delete = Training.objects.get(resource_id=resources_ids)
                        document_to_delete.is_deleted = True
                        document_to_delete.save()
                        return None
                    logger.debug(u'Error while querying, {0}/{1} try in exponential backoff mode'.format(n, 5))
                    time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
            LoggingHelper.getErrorLogger().error(u'There has been an error, the request never succeeded.')
            
            return None
        elif isinstance(resources_ids, Iterable):
            logger.debug(u'More than one resource to query, creating BatchFeed')

            request_feeds = []
            pool = multiprocessing.Pool()

            for i in range(0, len(resources_ids), 1000):
                chunk_resources_ids = resources_ids[i:i + 1000]

                request_feed = BatchHttpRequest(batch_response)
                for resource_id in chunk_resources_ids:
                    logger.debug(u'Adding query entry for resource %s', resource_id)
                    request_feed.add(client.files().get(fileId=resource_id))
                request_feeds.append(request_feed)

            logger.debug(u'Request to Google Drive')
            responses_feed = pool.map(crawl, request_feeds)
            pool.close()
            pool.join()

            full_response_feed = []
            """
            for response in response_feed:
                full_response_feed.extend(response_feed)

            if full_response_feed:
                resources_ids_to_delete = []
                resources_ids_in_error = []

                for entry in full_response_feed:
                    batch_status_code = int(entry.batch_status.code)
                    resource_id = entry.id.text.split('/')[5].replace('%3A',':')

                    if int(batch_status_code) == 404:
                        resources_ids_to_delete.append(resource_id)
                        full_response_feed.remove(entry)
                    elif int(batch_status_code) == 500:
                        resources_ids_in_error.append(resource_id)
                        full_response_feed.remove(entry)

                if len(resources_ids_to_delete):
                    Training.objects.filter(resource_id__in=resources_ids_to_delete).update(is_deleted=True, is_displayed=False, is_live=False, is_featured=False)

                if len(resources_ids_in_error):
                    logger.debug(u'%s entries in error', len(resources_ids_in_error))
                    time.sleep(2 + (random.randint(0, 1000) / 1000))

                    results_last_error = GoogleDriveHelper._query_resources_batch(resources_ids_in_error)
                    if isinstance(results_last_error, Iterable):
                        full_response_feed.extend(results_last_error)
                    else:
                        full_response_feed.append(results_last_error)
            """
        else:
            raise ValueError('Resources IDs parameter must be a string or a list')

        return response_feed

    @staticmethod
    def _build_document_json(document):
        """
        Return a document in JSON
        
        Args:
        user: User to match with
        document : A UniShared document
        """
        if document.type in ('document', 'application/vnd-mindmeister', 'presentation') :
            creator = ProfileHelper.get_user_json(document.creator)
            cowriters = [ProfileHelper.get_user_json(cowriter) for cowriter in document.cowriters.all()]
            participants = [{'id': participant.id} for participant in document.participants.all()]

            document_json = {'resource' : { 'id' : document.resource_id, 'type' : document.type, 'title' : unicode(document.title), 'updated' : document.last_updated}, 'creator' : creator, 'cowriters' : cowriters, 'participants': participants}
            if document.total_views > 0:
                document_json['resource'].update({'views': document.total_views})

            return document_json

    @staticmethod
    def share_to(resource_id, **kwargs):
        """
        Share a document to user, identified by email
        
        Args:
        resource_id : Resource's ID to share
        """
        client = GoogleDriveHelper.get_docs_client()
        logger = LoggingHelper.getDebugLogger()

        if resource_id:
            emails = kwargs.pop('emails', None)
            with_default_entry = kwargs.pop('with_default_entry', False)
            role = kwargs.pop('role', 'writer')

            if with_default_entry:
                logger.debug('Add default permission on document {0}'.format(resource_id))
                default_entry = {
                    'type' : 'anyone',
                    'role' : 'writer',
                    'withLink': 'true'
                }

                client.permissions().insert(fileId=resource_id, body=default_entry, sendNotificationEmails=False).execute()

            for email in emails:
                logger.debug('Add permission {0} for {1} on document {2}'.format(role, email, resource_id))
                acl_entry = {
                    'type' : 'user',
                    'value' : email,
                    'role' : role
                }
                client.permissions().insert(fileId=resource_id, body=acl_entry, sendNotificationEmails=False).execute()

    @staticmethod
    def check_unistar_folder(username):
        """
        Check if a UniStar's collection exist

        Args:
        username: UniStar's username
        """
        logger = LoggingHelper.getDebugLogger()
        client = GoogleDriveHelper.get_docs_client()

        folder_name = GoogleDriveHelper._get_unistar_collection_name(username)

        params={
            "q":"title='{0}' and '{1}' in parents".format(folder_name, settings.DRIVE_ROOT_FOLDER_ID)
        }

        logger.debug('Looking for Drive folder {0}'.format(folder_name))
        result = client.files().list(**params).execute()

        if result and len(result['items']):
            logger.debug('Folder {0} found'.format(folder_name))
            return result['items'][0]
        else:
            logger.debug('Folder {0} not found'.format(folder_name))
            return None

    @staticmethod
    def create_unistar_folder(user):
        """
        Create a UniStar collection

        Args:
        username: UniStar's username
        """
        logger = LoggingHelper.getDebugLogger()
        client = GoogleDriveHelper.get_docs_client()
        folder_name = GoogleDriveHelper._get_unistar_collection_name(user.username)

        logger.debug('Creating folder {0}'.format(folder_name))
        folder = client.files().insert(body={
            "title": folder_name,
            "parents": [{"id": settings.DRIVE_ROOT_FOLDER_ID}],
            "mimeType": "application/vnd.google-apps.folder"
        }).execute()

        return folder['id']

    @staticmethod
    def create_new_document(user, title):
        """
        Create a new GDocs document

        Args:
        user: the user who created the document.
        title: document's title
        """
        logger = LoggingHelper.getDebugLogger()
        client = GoogleDriveHelper.get_docs_client()

        new_doc_drive = None
        logger.debug(u'Creating new document with title {0}'.format(title))
        for n in range(0, 5):
            try:
                body = {
                    'title': title,
                }
                new_doc_drive = client.files().copy(fileId='1SNXug-TzAPChlspn9EKKmUBvRohlkY08CbNoxZAfPbY', body=body).execute()

                break
            except errors.HttpError:
                time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
                    
        if not new_doc_drive:
            LoggingHelper.getErrorLogger.error('Something wrong happened, the creation request never succeeded.')
            return None

        #is_displayed = title.lower() not in GoogleDriveHelper.TITLE_FILTER
        document_type = 'document'
        document_id = new_doc_drive['id']
        document_unishared = Training.objects.create(type=document_type, resource_id=document_id, creator=user, last_updated=time.time(), title=title, is_displayed=False)

        return document_unishared

    @staticmethod
    def delete_document(resource_id):
        """
        Delete a document.
        In fact, copy the document in a special collection
        
        Args:
        resource_id: resource's id to delete
        """
        try:
            logger = LoggingHelper.getDebugLogger()
            client = GoogleDriveHelper.get_docs_client()
            document_model = Training.objects.get(resource_id=resource_id)
            
            logger.debug('Delete resource {0}'.format(resource_id))

            logger.debug('Creating a copy of resource {0} and moving to trashbin folder'.format(resource_id))
            body = {
                'title' : document_model.title,
                'parents': [{'id': settings.DRIVE_TRASHBIN_FOLDER_ID}]
            }
            doc_copy = client.files().copy(fileId=resource_id, body=body).execute()

            logger.debug('Delete the original document {0}'.format(resource_id))
            client.files().trash(fileId=resource_id).execute()

            logger.debug('Flagging the document as deleted in DB {0}'.format(resource_id))
            document_model.is_deleted = True
            document_model.is_displayed = False
            document_model.resource_id = doc_copy['id']
            document_model.save()

            return True
        except Exception, e:
            LoggingHelper.getErrorLogger().error(e, exc_info=1)
            return False    
    
    @staticmethod
    def update_document(resource_id, **params):
        """
        Update a document
        
        Args:
        resource_id: Resource to update
        params: Parameters to update
        """
        try:
            client = GoogleDriveHelper.get_docs_client()
            client.files().update(fileId=resource_id, body=params)
        except Exception, e:
            LoggingHelper.getErrorLogger().error(e, exc_info=1)
            return False
        
class ProfileHelper():
    EMAIL_HOST_REGEX = re.compile(".*@(.*)$")
    GMAIL_SERVERS_REGEX = re.compile("(.google.com.|.googlemail.com.)$", re.IGNORECASE)
    
    @staticmethod
    def get_students_school(id_organization, filter_inactive):
        """
         Return all the students of a school
         Args:
         id_organization : Id of the organization
        """
        logger = LoggingHelper.getDebugLogger()

        organization_model = None
        try:
            organization_model = Organization.objects.get(id=id_organization)
            logger.debug(u'Organization found : {0}'.format(organization_model.name))
            organization_members = []
            organization_members_profile = UserProfile.objects.filter(organization=organization_model, isUniStar=True).select_related('user')
            for organization_member_profile in organization_members_profile:
                organization_members.append(organization_member_profile.user)
            if filter_inactive:
                organization_members_filtered = []
                for organization_member in organization_members:
                    if not organization_member.is_staff:
                        organization_members_filtered.append(organization_member)
                organization_members = organization_members_filtered

            return organization_model.members_role, organization_members
        except Organization.DoesNotExist:
            logger.debug('No organization found for {0}'.format(id_organization))
            return None, None
        except UserProfile.DoesNotExist:
            logger.debug('No students found for organization {0}'.format(organization_model.name))
            return None, None
    
    @staticmethod
    def update_profile(user_id, post_dict):
        """
        Update a UniStar profile

        Args:
        user_id: the UniStar's id
        post_dict: fields to update
        """
        logger = LoggingHelper.getDebugLogger()

        response_dict = {}

        if user_id is not None and user_id != '' and int(user_id) and user_id != 0:
            try:
                user = User.objects.get(id=user_id)
                user_profile = user.get_profile()
                logger.debug(u'Update {0}\'s (user_id: {1}) profile'.format(user.username, user.id))

                about_me = post_dict.get('about_me', None)
                if about_me:
                    logger.debug(u'Updating about_me')
                    user_profile.about_me = about_me
                    user_profile.save()
                    response_dict.update({'about_me' : {'success' : True}})
                
                is_student = post_dict.get('is_student', None)
                if is_student:
                    logger.debug(u'Updating is_student')
                    
                    user.get_profile().is_student = is_student == 'true'
                    user_profile.save()
                    response_dict.update({'is_student' : {'success' : True}})       
                
                school = post_dict.get('school', None)   
                if school:
                    logger.debug(u'Updating school')
                    
                    school = unicode(school)
                    organization = None
                    try:
                        organization = Organization.objects.get(name=school)                        
                    except Organization.DoesNotExist:
                        organization = Organization.objects.create(name=school, members_role = 'students')
                        
                    if organization:
                        user.get_profile().organization = organization  
                        user.get_profile().is_organization_verified = True
                        user_profile.save()    
                        response_dict.update({'school' : {'success' : True}})
                    else:
                        response_dict.update({'school' : {'success' : False}})

                email = post_dict.get('email', None)
                if email:
                    logger.debug(u'Updating email')
                    try:
                        f = forms.EmailField()
                        f.clean(email)

                        if user.get_profile().is_student and not ProfileHelper.is_gmail(email):
                            response_dict.update({'email' : {'success' : False, 'message' : 'Please provide a valid gmail address'}})
                        else:
                            user.get_profile().is_email_verified = True
                            user.get_profile().save()
                            user.email = email
                            user.save()
                            response_dict.update({'email' : {'success' : True, 'message' : 'Your email has been saved. Ready to UniShare!'}})
                    except forms.ValidationError:
                        logger.debug("Error : Wrong email format : %s", email)
                        response_dict.update({'email' : {'success' : False, 'message' : 'Wrong email format'}})

                enable_notifications = post_dict.get('enable_notifications', None)
                if isinstance(enable_notifications, bool):
                    logger.debug('Updating with notifications')

                    user_profile.enable_notifications = enable_notifications
                    user_profile.save()
            except User.DoesNotExist:
                response_dict.update({'user' : {'success' : False, 'message' : 'This user does not exist'}})
        else:
            response_dict.update({'id': {'success' : False, 'message' : 'Incorrect ID'}})

        is_student_save_ok = True
        if 'is_student' in response_dict:
            is_student_save_ok = response_dict['is_student']['success']

        is_school_save_ok = True
        if 'school' in response_dict:
            is_school_save_ok = response_dict['school']['success']    
            
        is_email_save_ok = True
        if 'email' in response_dict:
            is_email_save_ok = response_dict['email']['success']
            
        response_dict.update({'success' : is_student_save_ok and is_school_save_ok and is_email_save_ok })
        return response_dict

    @staticmethod
    def get_profile_url(username):
        return '{0}{1}'.format(settings.BASE_URL, reverse('website.views.profile', kwargs={'user_id': username}))
    """
    @staticmethod
    def proceed_education(user_profile, education):
        logger = LoggingHelper.getDebugLogger()

        last_school = None
        if education is not None:
            last_year = 0
            for school in education:
                logger.debug('school found : %s', school['school']['name'])
                if 'year' in school and 'name' in school['year'] and 'type' in school:
                    logger.debug('year\'s school : %s', school['year']['name'])
                    if school['type'] == 'College' and school['year']['name'] > last_year:
                        logger.debug('school year\'s (%s) > actual school year (%s)', school['year']['name'], last_year)
                        last_school = school

                        last_year = school['year']['name']
                        logger.debug('update last year : %s', last_year)

        if last_school is not None:
            logger.debug('Last school not None : %s', last_school['school']['name'])
            university_model = None
            try:
                logger.debug('looking for a university model for : %s', last_school['school']['name'])
                if last_school['school']['name'].startswith('ESCP'):
                    logger.debug('Special case of ESCP : all schools which are starting by ESCP are ESCP Europe')
                    university_model = University.objects.get(name='ESCP Europe')
                else:
                    university_model = University.objects.get(name=last_school['school']['name'])
                    
                logger.debug('University Model found !')
            except University.DoesNotExist:
                logger.debug('Not any university model found, creating one')
                university_model = University.objects.create(name=last_school['school']['name'], country=None)

            if user_profile.university_id != university_model.id:
                logger.debug('University model different from previous one, updating the model')
                user_profile.university_id = university_model.id
                user_profile.save()
    """        
    @staticmethod
    def get_user_json(user, picture_size='32x32'):
        """
        Return a user in JSON
        
        Args:
        user: The user to serialize in JSON
        picture_size: Profile picture size
        """
        im = None

        # Workaround for the moment : inactive with website url = partner
        if not user.is_active and user.get_profile().website_url:
            profile_link = user.get_profile().website_url
            if user.get_profile().image:
                try:
                    im = get_thumbnail(user.get_profile().image, '90x90', quality=99)
                except IOError:
                    logging.warn('Profile image not found for user {0}'.format(user.id))
        else:
            profile_link = reverse('website.views.profile', kwargs={'user_id': user.username})
            if user.get_profile().image:
                try:
                    im = get_thumbnail(user.get_profile().image, picture_size, crop='center', quality=99)
                except IOError:
                    logging.warn('Profile image not found for user {0}'.format(user.id))
        user_json = { "id" : user.id, "username": user.username, "first_name": user.first_name, "facebook_id" : user.get_profile().facebook_id, "profile_link" : profile_link}
        if 'im' in locals() and im and im.url:
            user_json.update({"picture": im.url})

        return user_json

    @staticmethod
    def is_login_completed(user):
        """
        Check if the login is completed
        
        Args:
        user: The user to check
        """
        if user.get_profile().is_student is None:
            return False
        elif user.get_profile().is_student is False and not user.get_profile().is_email_verified:
            return False
        elif user.get_profile().is_student and (user.get_profile().is_organization_verified is False or user.get_profile().is_email_verified is False):
            return False
        else:
            return True
    
    @staticmethod
    def is_gmail(email):
        """
        Returns True if the supplied Email address is a @gmail.com Email or is a Google Apps for your domain - hosted Gmail address
        Checks are performed by checking the DNS MX records 
        """
        m = ProfileHelper.EMAIL_HOST_REGEX.findall(email)
        if m and len(m) > 0:
                host = m[0]
                if host and host != '':
                    host = host.lower()

                if host == "gmail.com":
                    return True
                else:
                    try:
                        answers = dns.resolver.query(host, 'MX')
                        for rdata in answers:
                                m = ProfileHelper.GMAIL_SERVERS_REGEX.findall(str(rdata.exchange))
                                if m and len(m) > 0:
                                        return True
                    except Exception:
                        return False

        return False
        
class LoggingHelper():
    @staticmethod
    def getDebugLogger():
        return logging.getLogger('unishared.debug')
    
    @staticmethod
    def getErrorLogger():
        return logging.getLogger('unishared.error')
    
class SessionHelper():
    @staticmethod
    def get_key_from_session(session_key, key, wait=True, delete=False, noneAccepted = False):
        """
        Retrieve keys from session
        Wait MAX_LOOP * TIME_WAIT seconds
        
        Args:
        session_key : session to explore
        key : key to retrieve
        wait : wait during 2 minutes
        delete : delete key in session
        noneAccepted : return none value
        """
        if wait:
            starttime = time.time()
            timeout = 120
            
        result = None
        
        while True:
            session_models = Session.objects.filter(session_key=session_key)
            if session_models.exists():
                session_model = session_models[0]
                session_data = session_model.get_decoded()

                if key in session_data:
                    if session_data[key] or noneAccepted:
                        result = session_data[key]
                    if delete:
                        del session_data[key]
                        session_model.session_data = SessionStore().encode(session_data)

                if not result:
                    if wait:
                        if starttime + timeout < time.time():
                            break
                        else:
                            time.sleep(1)
                    else:
                        break
                else:
                    break
        return result

    @staticmethod
    def put_key_value_in_session(session_key, **kwargs):
        """
        Write key/value in session
        
        Args:
        session_key : Session to write
        kwargs : keys/values to write in session
        """
        session_model = Session.objects.select_for_update().filter(session_key=session_key)[0]
        session_data = session_model.get_decoded()   
        for keyValue in kwargs.iteritems():
            session_data[keyValue[0]] = keyValue[1]
        session_model.session_data = SessionStore().encode(session_data)
        session_model.save()
        
    @staticmethod
    def remove_key_in_session(session_key, *args):
        """
        Write key in session
        
        Args:
        session_key : Session to update
        kwargs : keys to remove in session
        """
        session_model = Session.objects.select_for_update().filter(session_key=session_key)[0]
        session_data = session_model.get_decoded()   
        for key in args:
            if key in session_data:
                del session_data[key]
        session_model.session_data = SessionStore().encode(session_data)
        session_model.save()

class MissingConnectionException(Exception):
    pass
  
from django.core.files.images import ImageFile
def _get_image_dimensions(self):
    if not hasattr(self, '_dimensions_cache'):
        #if getattr(self.storage, 'IGNORE_IMAGE_DIMENSIONS', False):
        self._dimensions_cache = (0, 0)
        #else:
        #    close = self.closed
        #    self.open()
        #    self._dimensions_cache = get_image_dimensions(self, close=close)
    return self._dimensions_cache
ImageFile._get_image_dimensions = _get_image_dimensions
