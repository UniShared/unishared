#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import timedelta
import json
import urllib2
from dateutil.parser import parse

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.core.urlresolvers import reverse
from django.conf import settings as django_settings
from django.core.validators import email_re
from django.utils.hashcompat import md5_constructor as md5
from django.db.models import Q
from django.http import *
from django.shortcuts import render_to_response
from django.template import Context, RequestContext
from django.core.cache import cache
from django.utils.html import escape
from django.views.decorators.http import require_http_methods, require_safe, require_GET
from oauth2client import xsrfutil
from oauth2client.django_orm import Storage

from UniShared_python.website.tasks import email_task, facebook_task, document_temp_share_task, acl_feed_task, move_document_to_user_folder
from helpers.helpers import GoogleDriveHelper, ProfileHelper, \
    SessionHelper
from models import Training, TrainingTempShare, TrainingSchedule, UserProfile, \
    Hub, HubPermissions, NoteTakingBuddy, CredentialsModel

from website.forms import NoteTakingBuddyForm

from helpers.helpers import LoggingHelper

@require_safe
def home(request):
    """
    Home view
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('website.views.profile', kwargs={'user_id': request.user.username}))
    else:
        return render_to_response('index.html', context_instance=RequestContext(request))

@require_safe
def about(request):
    """
    About view (same as home but don't care about user authentification)
    """
    return render_to_response('index.html', context_instance=RequestContext(request))

@require_safe
def videonotes(request):
    """
    Redirect to VideoNot.es
    """
    return HttpResponseRedirect('https://chrome.google.com/webstore/detail/videonotes/gfpamkcpoehaekolkipeomdbaihfdbdp')

@require_safe
def qrcode(request):
    return HttpResponseRedirect('http://checkthis.com/mdtj')

@require_GET
def policy(request):
    return render_to_response('privacy-policy.html', context_instance=RequestContext(request))

@require_safe
def partners(request):
    return render_to_response('partners.html', context_instance=RequestContext(request))

@require_safe
def hubs(request):
    return HttpResponseRedirect('http://checkthis.com/zrrv')
    #hubs_profiles = UserProfile.objects.filter(isUniStar=False).select_related('user')
    
    #return render_to_response('hubs.html', {'hubs_profiles' : hubs_profiles }, context_instance=RequestContext(request))

@require_safe
def yyprod(request):
    return render_to_response('yyprod.html', context_instance=RequestContext(request))

@require_GET
def login_session(request):
    """
    Login view to go to a document
    """
    return render_to_response('registration/login-session.html', context_instance=RequestContext(request))

@require_GET
def login_error(request):
    """
    View for a login error
    """
    
    return render_to_response('registration/login_error.html', context_instance=RequestContext(request))

@require_GET
def sign_off(request):
    """
    View for sign-off
    """
    
    logout(request)
    
    return HttpResponseRedirect(reverse('website.views.home'))

@require_GET
@login_required
def settings(request):
    """
    Settings view
    """
    education = []

    if request.user.get_profile().organization:
        education.append(request.user.get_profile().organization.name)
    return render_to_response('registration/login.html', {'title': 'Settings', 'with_student_lifelonglearner': True, 'with_organization' : True, 'education': education, 'with_email' : True}, context_instance=RequestContext(request))

@require_GET
def disable_emails_notifications(request):
    """
    Disable all emails for current user
    """
    ProfileHelper.update_profile(request.user.id, {'enable_notifications': False})

    return render_to_response('mails/disable_emails_notifications.html', context_instance=RequestContext(request))

@require_safe
def open25_leadboard(request):
    """
    Processing the Open 25 leadboard
    """
    cache_key = 'open25-leaderboard'
    leaderboard = cache.get("open25-leaderboard")

    if not leaderboard:
        users_points = {}

        def store_user_points(user):
            username = user.username
            if user.get_profile().isUniStar and username not in ['clementdelangue', 'arnaud.breton']:
                user_json = ProfileHelper.get_user_json(user, '90x90')
                if username in users_points:
                    users_points[username] = (user_json, users_points[username][1] + document.total_views_open25)
                else:
                    users_points[username] = (user_json, document.total_views_open25)

        documents = Training.objects.batch_select('cowriters').filter(total_views_open25__gt=0)
        for document in documents:
            store_user_points(document.creator)
            for cowriter in document.cowriters_all:
                store_user_points(cowriter)

        leaderboard = OrderedDict(sorted(users_points.items(), key=lambda t: t[1][1], reverse=True)).items()[:30]
        cache.set(cache_key, leaderboard, 60*60)

    return render_to_response('open25-leadboard.html', {'users_points': leaderboard}, context_instance=RequestContext(request))

@require_http_methods(['GET', 'POST'])
def login(request):
    """
    Login view
    """    
    if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('socialauth_begin', kwargs={'backend': 'facebook'}))
    else:
        if request.method == 'POST':
            response_dict = ProfileHelper.update_profile(request.user.id, request.POST)
            return HttpResponse(content=json.dumps(response_dict),
                   mimetype="application/json", status=200)
        elif request.method == 'GET':
            user = User.objects.get(id=request.user.id)
            education = None
            if 'education' in request.session:
                if request.session.get('education') is not None:
                    education = request.session.get('education')
                    def sort_education(x):
                        if 'year' in x and 'name' in x['year']:
                            return x['year']['name']
                        else:
                            return x['school']['name']
                    education.sort(key=lambda x : sort_education(x), reverse=True)
                    education = [school['school']['name'] for school in education]
            
            is_organization_verified = user.get_profile().is_student is False or (user.get_profile().is_student and user.get_profile().is_organization_verified)
            template = render_to_response('registration/login.html', {'title': 'Login', 'education' : education, 'with_student_lifelonglearner': request.user.get_profile().is_student is None, 'with_organization' : not is_organization_verified, 'with_email' : not user.get_profile().is_email_verified}, context_instance=RequestContext(request))
            profile = reverse('website.views.profile', kwargs={'user_id': user.username})
            
            if user.get_profile().is_student is None:
                return template
            else:
                if user.get_profile().is_student:
                    if user.get_profile().is_email_verified and user.get_profile().is_organization_verified:
                        if 'education' in request.session:
                            del request.session['education']
                            
                        if 'next' in request.GET:
                            return HttpResponseRedirect(request.GET['next'])
                        else:
                            return HttpResponseRedirect(profile)
                    else:
                        return template
                else:
                    if user.get_profile().is_email_verified:
                        if 'next' in request.GET:
                            return HttpResponseRedirect(request.GET['next'])
                        else:
                            return HttpResponseRedirect(profile)
                    else:
                        return template

@require_http_methods(['GET', 'POST'])
def profile(request, user_id=None):
    """
    Profile view
    
    Args: 
    user_id: User's ID
    """
    if request.method == 'GET':
        is_my_profile = False

        # To keep compatibility with the old URL format
        id_get = request.GET.get('id', None)

        if id_get is not None:
            user_id = id_get

        if user_id is None or user_id == '' or id <= 0:
            if request.user.is_anonymous():
                return HttpResponseRedirect(reverse('website.views.login'))
            else:
                user_profile = request.user
                is_my_profile = True
        else:
            try:
                try:
                    id_int = int(user_id)
                    user_profile = User.objects.get(id=id_int, is_active=True)
                    is_my_profile = (id_int == request.user.id)
                except ValueError:
                    user_profile = User.objects.get(username__iexact=user_id, is_active=True)
                    is_my_profile = (user_id == request.user.username)
            except User.DoesNotExist:
                return render_to_response('error.html', { 'error' : u'This profile does not exist.'}, context_instance=RequestContext(request))

        if is_my_profile and not ProfileHelper.is_login_completed(user_profile):
            return HttpResponseRedirect(reverse('website.views.login'))

        if user_profile.get_profile().isUniStar:
            documents_count = Training.objects.filter(Q(creator=user_profile) | Q(participants=user_profile) | Q(cowriters=user_profile), is_deleted=False).exists()
            return render_to_response('accounts/profile.html', {'is_my_profile' : is_my_profile, 'user_profile' : user_profile, 'documents_count': documents_count}, context_instance=RequestContext(request))
        else:
            first_creation = False
            coming_from_creation_view = ('HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].find(reverse('website.views.create_hub')) > -1)
            if coming_from_creation_view:
                first_creation = Hub.objects.filter(moderator=request.user).count() == 1

            if user_profile.get_profile().organization and user_profile.get_profile().organization.members_role == 'students':
                is_my_profile = not request.user.is_anonymous() and request.user.get_profile().organization == user_profile.get_profile().organization
                members_role = user_profile.get_profile().organization.members_role
            else:
                hub = Hub.objects.get(user=user_profile)
                hub_perms = HubPermissions.objects.filter(hub=hub)

                if hub_perms.exists():
                    is_my_profile = not request.user.is_anonymous() and request.user.id in hub_perms
                else:
                    is_my_profile = True

                if user_profile.get_profile().organization:
                    members_role = hub.user.get_profile().organization.members_role
                else:
                    members_role = 'participants'

            return render_to_response('hub/hub.html', {'user_profile' : user_profile, 'members_role' : members_role, 'is_my_profile' : is_my_profile, 'first_creation': first_creation}, context_instance=RequestContext(request))

    elif request.method == 'POST' and request.is_ajax():
        if user_id is None or user_id == '' or user_id <= 0:
            if request.user.is_anonymous():
                HttpResponseRedirect(reverse('website.views.login'))
            else:
                response_dict = ProfileHelper.update_profile(request.user.id, request.POST)
                return HttpResponse(content=json.dumps(response_dict),
                   mimetype="application/json", status=200)

def redirect_to_notes(request, action):
    """
    Redirect the old "class" URL to the new "notes" URL
    """
    return HttpResponsePermanentRedirect('/notes/{0}'.format(action))

@require_GET
def activity(request, user_id, objects):
    """
    Activity view which is returning all the documents, order by last modification date
    
    Args:
    user_id: User's ID
    """
    logger = LoggingHelper.getDebugLogger()
    try:
        id_page = int(request.GET.get('page', '1'))
    except ValueError:
        id_page = 1

    try:
        max_items = int(request.GET.get('max_items', '50'))
    except ValueError:
        return HttpResponseServerError()

    query = request.GET['q'] if 'q' in request.GET else ''
    title_only = request.GET['titleOnly'] if 'titleOnly' in request.GET else False

    cache_duration = -1

    try:
        int(user_id)
        cache_duration = 60*15
    except ValueError:
        user_id_cache_duration = [('all', 60 * 60), ('featured', 0)]
        cache_duration_list = [a[1] for a in user_id_cache_duration if user_id == a[0]]
        if len(cache_duration_list):
            cache_duration = cache_duration_list[0]

    cache_key = 'user_id-{0}_{1}_page-{2}-max_items-{3}'.format(user_id, objects, id_page, max_items)
    if query:
        cache_key = '_'.join([cache_key,'query-{0}'.format(md5(query.encode('utf-8')).hexdigest())])

    full_response = cache.get(cache_key) if cache_duration >= 0 else None

    if not full_response:
        logger.debug('No cache for key {0}'.format(cache_key))

        if objects == 'documents':
            if user_id == 'all':
                total_records, response = GoogleDriveHelper.get_all_documents(max_documents=max_items, id_page=id_page, user=request.user, query=query, title_only=title_only)
            elif user_id == 'live':
                total_records, response = GoogleDriveHelper.get_all_documents(max_documents=max_items, live_only=True)
            elif user_id == 'featured':
                total_records, response = GoogleDriveHelper.get_all_documents(max_documents=max_items, id_page=id_page, featured_only=True)
            else:
                user = User.objects.get(id=user_id)
                total_records, response = GoogleDriveHelper.get_all_user_documents(user, max_documents=max_items, id_page=id_page, query=query, title_only=title_only)

            response = [GoogleDriveHelper._build_document_json(document) for document in response]
        elif objects == 'hubs':
            if user_id == 'featured':
                hubs_profiles = Hub.objects.filter(is_featured=True, is_displayed=True, user__is_active=True).select_related('user')
            elif user_id == 'live':
                hubs_profiles = Hub.objects.filter(is_live=True, is_displayed=True, user__is_active=True).select_related('user')
            else:
                if query:
                    hubs_profiles = Hub.search(query)
                else:
                    hubs_profiles = Hub.objects.filter(is_displayed=True, user__is_active=True).select_related('user')

            response = []
            for hub_profile in hubs_profiles:
                hub_json = ProfileHelper.get_user_json(hub_profile.user)

                hub_documents = Training.objects.batch_select('cowriters', 'participants').filter(Q(creator=hub_profile.user) | Q(cowriters=hub_profile.user), is_deleted=False).distinct('creator','cowriters')

                cowriters = []
                participants = []
                last_updated = hub_profile.user.date_joined.strftime('%s')

                for hub_document in hub_documents:
                    if hub_document.last_updated > last_updated:
                        last_updated = hub_document.last_updated

                    if hub_document.creator != hub_profile.user and hub_document.creator.get_profile().isUniStar:
                        cowriters.append(ProfileHelper.get_user_json(hub_document.creator))

                    cowriters.extend([ProfileHelper.get_user_json(cowriter) for cowriter in hub_document.cowriters_all if cowriter != hub_profile.user and cowriter.get_profile().isUniStar])
                    participants.extend([{'id': participant.id} for participant in hub_document.participants_all])

                hub_json.update({'cowriters': cowriters})
                hub_json.update({'participants': participants})
                hub_json.update({'last_updated': last_updated})
                response.append(hub_json)

            paginator = Paginator(response, max_items)

            try:
                page = paginator.page(id_page)
            except (EmptyPage, InvalidPage):
                page = paginator.page(1)

            total_records = len(response)
            response = sorted(page.object_list, key=lambda t: t['last_updated'], reverse=True)

        full_response = {'totalRecords': total_records, objects: response}
        if cache_key and cache_duration >= 0:
            logger.debug('Caching {0} for {1} seconds'.format(cache_key, cache_duration))
            cache.set(cache_key, full_response, cache_duration)

    return HttpResponse(content=json.dumps(full_response),
        mimetype="application/json", status=200)

@require_safe
def embedded_document(request, resource_id):
    """
    Redirect to a document.
    Registering Google Analytics' open event.
    
    Args:
    resource_id: resource's id to redirect
    """
    logger = LoggingHelper.getDebugLogger()

    try:
        if not resource_id:
            result = SessionHelper.get_key_from_session(request.session.session_key, 'resource_id')

            if result:
                resource_id = result
                return HttpResponseRedirect(reverse('website.views.embedded_document', kwargs={'resource_id': resource_id}))
            else:
                return HttpResponseBadRequest()

        document = Training.objects.get(resource_id=resource_id, is_deleted=False)
        document_url = GoogleDriveHelper.get_document_url(document.resource_id)

        first_creation = False
        first_participation = False

        # Returning Open graph meta data if Facebook's / Google's scraper
        if 'HTTP_USER_AGENT' in request.META and request.META['HTTP_USER_AGENT'] in ('facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)', 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)') :
            logger.debug('Request from %s', request.META['HTTP_USER_AGENT'])
            return render_to_response('document/document.html', {'footer' : False, 'scraper' : True, 'document' : document}, context_instance=RequestContext(request))
        elif not request.user.is_anonymous():
            coming_from_creation_view = ('HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].find(reverse('website.views.create_document')) > -1)
            if coming_from_creation_view:
                first_creation = Training.objects.filter(creator=request.user, is_deleted=False).count() == 1
            else:
                if request.user == document.creator or request.user in document.cowriters.all():
                    facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, 'cowrite'), {django_settings.FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE : document_url}])
                else:
                    facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, 'participate'), {django_settings.FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE : document_url}])
                    first_participation = not Training.objects.filter(participants=request.user).exists()

                document_temp_share_task.apply_async([document, request.user])

        can_invite_cowriters = (request.user == document.creator or request.user in document.cowriters.all())

        if 'HTTP_USER_AGENT' in request.META:
            mobiles_users_agents = ('Android','iPad','iPhone','BlackBerry', 'PlayBook', 'MeeGo')

            for mobile_user_agent in mobiles_users_agents:
                if mobile_user_agent in request.META['HTTP_USER_AGENT']:
                    return HttpResponseRedirect('https://docs.google.com/{0}/d/{1}/edit'.format(document.type, document.resource_id))

        if request.user == document.creator or request.user in document.cowriters.all():
            share_text_twitter =  u'I\'m taking notes about {0}, join me and contribute:'.format(document.title[:56])
        else:
            share_text_twitter = u'I\'m in a note-taking session about {0}, join me and contribute:'.format(document.title[:44])

        return render_to_response('document/document.html', {'footer' : False, 'document' : document, 'nb_views': document.total_views, 'first_creation': first_creation,'first_participation': first_participation, 'can_invite_cowriters' : can_invite_cowriters, 'share_text_twitter': share_text_twitter}, context_instance=RequestContext(request))
    except Training.DoesNotExist:
        logger.debug(u'Unexisting document : {0}'.format(resource_id))
        raise Http404()
    except Exception:
        LoggingHelper.getErrorLogger().error('An error occurred while accessing to a document (resource_id: {0}'.format(resource_id), exc_info=1)
        return render_to_response('document/error.html', {'resource_id': resource_id}, context_instance=RequestContext(request))

@login_required
@require_http_methods(['GET', 'POST'])
def create_document(request):
    """
    Create a new document
    """

    if not request.user.get_profile().can_create:
        return render_to_response(u'error.html', { u'error' : u'You cannot create document'})

    if request.method == 'GET':
        #if not ProfileHelper.is_login_completed(request.user):
        #    return HttpResponseRedirect(reverse('website.views.login') + '?next=' + request.get_full_path())
        if 'from' in request.GET and request.GET[u'from']:
            try:
                hub = Hub.objects.get(user__id=request.GET[u'from'])
            
                # Creation docs from another user is allowed when:
                # From a hub
                # Is the user university's hub
                # Is a hub where the user is allowed

                if hub.user.get_profile().organization and hub.user.get_profile().organization.members_role == 'students':
                    allow_to_create_from = request.user.get_profile().organization == hub.user.get_profile().organization
                else:
                    hub_perms = HubPermissions.objects.filter(hub=hub)
                    allow_to_create_from = not hub_perms.exists() or hub_perms.filter(allowed_user_id=request.user.id).exists()
                     
                if not allow_to_create_from:
                    return render_to_response(u'error.html', { u'error' : u'You cannot create document from this profile'}) 
            except User.DoesNotExist:
                return render_to_response('error.html', { 'error' : u'This profile does not exist.'}, context_instance=RequestContext(request))   
        
        SessionHelper.remove_key_in_session(request.session.session_key, 'resource_id')
        return render_to_response('document/create_a_document.html', context_instance=RequestContext(request))
    elif request.method == 'POST':
        logger = LoggingHelper.getDebugLogger()

        if u'document_title' in request.POST:
            document_title = unicode(request.POST[u'document_title'])
            
            result = SessionHelper.get_key_from_session(request.session.session_key, 'resource_id', wait=False, noneAccepted=True)
            if result:
                """
                if not result:
                    result = SessionHelper.get_key_from_session(request.session.session_key, 'resource_id', noneAccepted=False)
                    if result:
                        logger.debug(u'Updating {0}\'s title {1}'.format(result, document_title))
                        GoogleDriveHelper.update_document(result, title=document_title)
                else:
                """
                logger.debug(u'Updating {0}\'s title {1}'.format(result, document_title))
                GoogleDriveHelper.update_document(result, title=document_title)

                return HttpResponse(status=200)
            else:         
                SessionHelper.put_key_value_in_session(request.session.session_key, resource_id=None)

                hub = None
                if 'from' in request.POST and request.POST['from']:
                    hub = Hub.objects.get(user__id=request.POST['from'])
                    
                    # Creation docs from another user is allowed when:
                    # From profile is not a UniStar (not a physical person)
                    # Is your university
                    # Is a public profile where you are allowed 

                    allow_to_create_from = True

                    if hub.user.get_profile().organization and hub.user.get_profile().organization.members_role == 'students':
                        allow_to_create_from = request.user.get_profile().organization == hub.user.get_profile().organization
                    else:
                        hub_perms = HubPermissions.objects.filter(hub=hub)
                        allow_to_create_from = not hub_perms.exists() or hub_perms.filter(allowed_user_id=request.user.id).exists()
                         
                    if not allow_to_create_from:
                        return HttpResponseForbidden()
                    
                    logger.debug(u'Creating a new document from {0} for user {1} with title {2}'.format(hub.user.username, request.user.id, document_title))
                    new_doc = GoogleDriveHelper.create_new_document(request.user, document_title)
                else:
                    logger.debug(u'Creating a new document for user {0} with title {1}'.format(request.user.id, document_title))
                    new_doc = GoogleDriveHelper.create_new_document(request.user, document_title)

                if new_doc:
                    # Sharing with Google Apps group and document creator
                    with_group = 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].find(reverse('website.views.create_document')) > 0
                    share_task = acl_feed_task.apply_async([request.user.email, new_doc.resource_id, with_group])

                    move_document_to_user_folder.apply_async([new_doc.resource_id, request.user])

                    if request.user.get_profile().organization:
                        try:
                            organization_user = UserProfile.objects.get(isUniStar=False, organization=request.user.get_profile().organization)
                            if hub and organization_user.user != hub:
                                new_doc.cowriters.add(organization_user.user)
                        except UserProfile.DoesNotExist:
                            logger.debug(u'Organization {0} does not have a hub on UniShared'.format(request.user.get_profile().organization.name))

                    context = Context({'creator': request.user, 'document' : {'url': GoogleDriveHelper.get_document_url(new_doc.resource_id), 'title' : document_title}})

                    # Invalidate cache
                    cache_key = 'user_id-{0}_{1}_page-{2}-max_items-{3}'.format(request.user.id, 'documents', 1, 11)
                    cache.delete(cache_key)

                    if (u'starting_now' in request.POST and not bool(int(request.POST[u'starting_now']))) and (u'starting_time' in request.POST and request.POST[u'starting_time']):
                        start_time = unicode(request.POST[u'starting_time'])
                        start_time_datetime = parse(unicode(start_time))

                        context['document'].update({'start_time': start_time_datetime})

                        if u'create_facebook_event' in request.POST and request.POST[u'create_facebook_event'] == u'true':
                            event_task = facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, 'events', {'name':u'{0} on UniShared'.format(document_title), 'start_time': start_time,'location': GoogleDriveHelper.get_document_url(new_doc.resource_id),'privacy_type':'OPEN'}])
                            event_task_result = event_task.get(timeout=60)
                            if event_task_result and 'id' in event_task_result:
                                event_id = event_task_result['id']
                                context['document'].update({'event_id': event_id})
                                TrainingSchedule.objects.create(training = new_doc, start_time=start_time_datetime, event_id=event_id)
                        else:
                            TrainingSchedule.objects.create(training = new_doc, start_time=start_time_datetime)

                        if (start_time_datetime - timezone.now()).seconds/3600.0 > 1:
                            email_task.apply_async([u'Reminder: 1 hour to go!', context, 'document_scheduled_reminder', [request.user.email]], eta=start_time_datetime - timedelta(hours=1))
                    if hub:
                        hub_context = context.__copy__()
                        hub_context.update({'hub': hub.user})

                        if not hub.user.email.endswith('unishared.com'):
                            hub_context.update({'ga_campaign_params' : 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=new_document_hub_mail'})
                            email_task.apply_async([u'New document on UniShared', hub_context, 'new_document_hub_mail_to_moderators', [hub.moderator.email]])
                        else:
                            email_task.apply_async([u'[{0}] New document on UniShared'.format(django_settings.ENV_NAME), hub_context, 'new_document_hub_mail_to_moderators', [manager[1] for manager in django_settings.MANAGERS], None, 'gmail'])

                        # Invalidate cache
                        cache.set('{0}_cowriters'.format(hub.user.id), None)
                        cache.delete(cache_key.format(hub.user.id, 'documents'))

                        new_doc.cowriters.add(hub.user)
                    else:
                        email_task.apply_async([u'[{0}] New document on UniShared'.format(django_settings.ENV_NAME), context, 'new_document_mail_to_moderators', [manager[1] for manager in django_settings.MANAGERS], None, 'gmail'])

                    if Training.objects.filter(creator=request.user).count() == 1:
                        template = 'new_first_document_mail'
                    else:
                        template = 'new_document_mail'

                    context.update({'ga_campaign_params' : 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=new_document_mail'})
                    email_task.apply_async([u'Yihaa, you created a collaborative document!', context, template, [request.user.email]])

                    share_task.get(timeout=60)

                    SessionHelper.put_key_value_in_session(request.session.session_key, resource_id=new_doc.resource_id)
                    return HttpResponse(content=json.dumps({'resource_id' : new_doc.resource_id}), mimetype="application/json")
                else:
                    LoggingHelper.getErrorLogger().error(u'Something went wrong while creating a new document (username : {0}, document_title : {1})'.format(request.user.username, document_title))
                    return HttpResponseServerError()
        else:
            return HttpResponseBadRequest()

@require_http_methods(['GET', 'POST'])
def cowriters_participants_document(request, role, resource_id):
    """
    List or add cowriters / participants to a document

    Args:
    role: cowriter/participant
    resource_id: the document where list/add role
    """
    logger = LoggingHelper.getDebugLogger()

    if not resource_id:
        result = SessionHelper.get_key_from_session(request.session.session_key, 'resource_id')
        if result:
            resource_id = result
        else:
            return HttpResponseServerError()
    try:    
        document = Training.objects.batch_select(role).get(resource_id=resource_id, is_deleted=False)
    except Training.DoesNotExist:
        LoggingHelper.getErrorLogger().error(u'No document retrieved (username : {0})'.format(request.user.username))
        return HttpResponseNotFound()

    role_is_cowriter = (role == 'cowriters')
    role_is_participant = (role == 'participants')

    if not role_is_cowriter and not role_is_participant:
        return HttpResponseBadRequest()

    if request.method == u'GET':
        people = []

        if role_is_cowriter:
            people.append(ProfileHelper.get_user_json(document.creator))
        people.extend([ProfileHelper.get_user_json(people_role) for people_role in getattr(document, role + '_all')])

        return HttpResponse(content=json.dumps({role : people}), mimetype="application/json")
    elif request.method == u'POST':
        if request.user.get_profile().can_create:
            return HttpResponse(content=json.dumps({'success': False, 'message' : 'User cannot invite'}), mimetype="application/json")
        if role_is_cowriter and not request.user.id == document.creator.id and request.user.id not in document.cowriters.all().values_list('id', flat=True):
            return HttpResponseForbidden()
        
        document_title = document.title
        document_url =  GoogleDriveHelper.get_document_url(document.resource_id)
        emails = set()

        def process_invitation(document, role, **kwargs):
            facebook_id = kwargs.get('facebook_id', None)
            email = kwargs.get('email', None)
            user = kwargs.get('user', None)

            try:
                document_temp_share = TrainingTempShare.objects.get(Q(facebook_id=facebook_id) & Q(email=email) & Q(user_invited=user), user_who_invites=request.user, training=document, role=role)

                if ((timezone.now() - document_temp_share.last_updated).seconds/3600.0) > 1:
                    logger.debug('Last invitation made more than one hour ago, email will be send')
                    send_notifications = True
                else:
                    logger.debug('Last invitation made less than one hour ago, email won\'t be send')
                    send_notifications = False

                document_temp_share.last_updated = timezone.now()
                document_temp_share.save()
            except TrainingTempShare.DoesNotExist:
                try:
                    if facebook_id:
                        user_associated = UserProfile.objects.select_related('user').get(facebook_id=facebook_id).user
                    elif email:
                        user_associated = User.objects.get(email=email)
                    elif user:
                        user_associated = user

                    if user_associated and not user_associated in getattr(document, role + '_all'):
                        document.cowriters.add(user)
                except (UserProfile.DoesNotExist, User.DoesNotExist):
                    TrainingTempShare.objects.create(training=document, user_who_invites=request.user, facebook_id=facebook_id, email=email, role=role)

                send_notifications = True

            return send_notifications

        # Facebook sharing
        # If user invited people: always publish a story where friends are tagged in
        people_facebook_ids_set = set()
        open_graph_action = 'cowrite' if role_is_cowriter else 'participate'
        if 'people_facebook_ids' in request.POST and request.POST['people_facebook_ids']:
            people_facebook_ids = request.POST['people_facebook_ids']
            people_facebook_ids_set.update(set(people_facebook_ids.split(',')))
            for people_facebook_id in people_facebook_ids_set:
                if people_facebook_id:
                    logger.debug('Inviting a friend via Facebook : {0}'.format(people_facebook_id))
                    try:
                        user_unishared = UserProfile.objects.get(facebook_id=people_facebook_id)
                        logger.debug('User with Facebook id {0} is on UniShared'.format(people_facebook_id))
                        if process_invitation(document, role, user=user_unishared.user):
                            emails.add(user_unishared.user.email)
                    except UserProfile.DoesNotExist:
                        logger.debug('User with Facebook id {0} is not on UniShared'.format(people_facebook_id))
                        process_invitation(document, role, facebook_id=people_facebook_id)

            if role_is_cowriter:
                facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, open_graph_action), {django_settings.FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE : document_url, 'tags' : request.POST['people_facebook_ids']}])
            else:
                facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, open_graph_action), {django_settings.FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE : document_url, 'tags' : request.POST['people_facebook_ids']}])

        elif request.user == document.creator.id:
            facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, 'create'), {django_settings.FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE : document_url}])

        # Email sharing
        if 'people_emails' in request.POST and request.POST['people_emails']:
            people_emails = request.POST['people_emails'].split(',')
            for people_email in people_emails:
                people_email = people_email.strip().lower()
                if email_re.match(people_email):
                    logger.debug('Inviting a friend by email : {0}'.format(people_email))
                    try:
                        user_unishared = User.objects.get(email=people_email)
                        logger.debug('User with email id {0} is on UniShared'.format(people_email))
                        if process_invitation(document, role, user=user_unishared):
                            emails.add(people_email)
                    except User.DoesNotExist:
                        logger.debug('User with email {0} is not on UniShared'.format(people_email))
                        if process_invitation(document, role, email=people_email):
                            emails.add(people_email)
                else:
                    logger.debug('Invalid email : {0}'.format(people_email))

        # UniShared sharing
        if 'cowriters' in request.POST and request.POST['cowriters']:
            people_unishared = User.objects.filter(id__in=urllib2.unquote(request.POST['cowriters']).split(','))
            for user_unishared in people_unishared:
                logger.debug('Inviting a friend via UniShared : {0}'.format(user_unishared.username))
                people_facebook_ids_set.add(user_unishared.get_profile().facebook_id)
                if process_invitation(document, role, user=user_unishared):
                    emails.add(user_unishared.email)

        try:
            event_id = TrainingSchedule.objects.get(training=document).event_id
            if event_id and len(people_facebook_ids_set):
                facebook_task.apply_async([request.user, event_id, 'invited', {'users': ', '.join(str(people_facebook_id) for people_facebook_id in people_facebook_ids_set)}])
        except TrainingSchedule.DoesNotExist:
            logger.debug('No schedule for {0}'.format(document.resource_id))

        if len(emails):   
            subject = u'{0} is inviting you to take open notes collaboratively'.format(request.user.first_name)
            context = Context({'first_name' : request.user.first_name, 'document': {'title': document_title, 'url' : document_url }, 'ga_campaign_params' : 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=invite_cowriters_email'})

            document_schedule = None
            try:
                document_schedule = TrainingSchedule.objects.get(training=document)
                if document_schedule.start_time > timezone.now():
                    context['document'].update({'start_time': document_schedule.start_time, 'event_id': document_schedule.event_id})
                else:
                    context['document'].update({'event_id': document_schedule.event_id})
            except TrainingSchedule.DoesNotExist:
                logger.debug('No schedule for document {0}'.format(document.resource_id))

            for email in emails:
                email_task.apply_async([subject, context, 'invite_cowriter_mail', [email]])
                if document_schedule and (document_schedule.start_time - timezone.now()).seconds/3600.0 > 1:
                    email_task.apply_async([u'Reminder: 1 hour to go!', context, 'document_scheduled_reminder', [email]], eta=document_schedule.start_time - timedelta(hours=1))
        return HttpResponse(content=json.dumps({'success': True, 'message' : '{0} invited'.format(role.capitalize())}), mimetype="application/json")
      
@login_required
@require_http_methods(['DELETE'])
def remove_document(request, resource_id):
    """
    View to DELETE one document
    Args:
    resource_id : resource's ID to delete
    """
    try:
        document = Training.objects.batch_select('cowriters','participants').get(resource_id=resource_id)
        cache_key = 'user_id-{0}_documents'
        is_displayed = document.is_displayed

        if request.user == document.creator:
            if not GoogleDriveHelper.delete_document(resource_id):
                return HttpResponseServerError()
        elif request.user in document.cowriters_all:
            document.cowriters.remove(request.user)
        elif request.user in document.participants_all:
            document.participants.remove(request.user)
        else:
            return HttpResponseForbidden()

        """
        # Invalidate cache
        if request.user == document.creator or request.user in document.cowriters_all:
            cache.delete(cache_key.format(document.creator.id))
            [cache.delete(cache_key.format(cowriter.id)) for cowriter in document.cowriters_all]
            [cache.delete(cache_key.format(participant.id)) for participant in document.participants_all]

            if is_displayed:
                cache.delete(cache_key.format('all'))
        else:
            # Invalidate cache
            cache.delete(cache_key.format(request.user.id))
        """
        return HttpResponse()
    except Training.DoesNotExist:
        return HttpResponseNotFound()

@require_safe
def note_taking_buddy(request, hub_id):
    """
    Start the note taking process

    Args:
    hub_id: The hub, representing a course's notes, to start the process from
    """
    logger = LoggingHelper.getDebugLogger()

    if hub_id:
        try:
            hub = Hub.objects.get(user__username=hub_id)
        except Hub.DoesNotExist:
            logger.debug('From id {0} is not a hub'.format(hub_id))
            raise Http404

        if len(request.GET) and request.user.is_authenticated():
            form = NoteTakingBuddyForm(request.GET)
        else:
            form = NoteTakingBuddyForm()

        return render_to_response('note_taking_buddy.html', {'form': form, 'from_hub': hub.user}, context_instance=RequestContext(request))
    else:
        return HttpResponseBadRequest()

@require_http_methods(['GET', 'HEAD', 'POST'])
def note_taking_buddy_results(request, user_id, hub_id):
    """
    Results of the note taking buddies algorithm

    Args:
    hub_id: The hub, representing a course's notes, to show results from
    user_id: The user to show results
    """
    logger = LoggingHelper.getDebugLogger()

    try:
        hub = Hub.objects.get(user__username=hub_id)
    except Hub.DoesNotExist:
        logger.debug('From id {0} is not a hub'.format(hub_id))
        raise Http404

    if user_id:
        try:
            user = User.objects.get(username__iexact=user_id)
        except User.DoesNotExist:
            raise Http404
    else:
        if request.user.is_authenticated():
            url = reverse('website.views.note_taking_buddy_results', args=[hub_id, request.user.username])
        else:
            url = reverse('website.views.note_taking_buddy', args=[hub.user.username])
        return HttpResponseRedirect(url)

    if request.method == 'POST':
        try:
            current_user = NoteTakingBuddy.objects.get(user=user, hub=hub)
            form = NoteTakingBuddyForm(data=request.POST, hub=hub, user=user, instance=current_user)
        except NoteTakingBuddy.DoesNotExist:
            form = NoteTakingBuddyForm(data=request.POST, hub=hub, user=user)

        if form.is_valid():
            form.save()
        else:
            # TODO: Create a real error page
            error_message = "Form invalid: {0}".format(form.errors)
            LoggingHelper.getErrorLogger().error(error_message)
            return HttpResponseBadRequest(content=error_message)

    user_buddies = None
    is_current_user_results = (request.user == user)
    try:
        current_user = NoteTakingBuddy.objects.get(user=user, hub=hub)
        user_buddies = NoteTakingBuddy.objects.filter(~Q(user=user) & Q(hub=hub)).select_related('user')[:10]
        user_buddies = sorted(user_buddies, key=lambda t: abs(t.score - current_user.score))
    except NoteTakingBuddy.DoesNotExist:
        if request.user.is_authenticated() and is_current_user_results:
            return HttpResponseRedirect(reverse('website.views.note_taking_buddy', args=[hub.user.username]))

    return render_to_response('note_taking_buddy_results.html', {'buddies': user_buddies, 'hub': hub, 'user_requested': user, 'is_current_user_results': is_current_user_results}, context_instance=RequestContext(request))

# Hubs related views
@require_safe
def hubs(request):
    return HttpResponseRedirect('http://checkthis.com/zrrv')

@require_http_methods(['GET', 'HEAD', 'POST'])
@login_required()
def create_hub(request):
    """
    View to create a Hub
    """

    if request.method in ['GET', 'HEAD']:
        if request.user.get_profile().can_create:
            return render_to_response('hub/create_hub.html', context_instance=RequestContext(request))
        else:
            return render_to_response(u'error.html', { u'error' : u'You cannot create hub'})

    elif request.method == 'POST':
        if request.user.get_profile().can_create:
            name = request.POST['hub_name'] if 'hub_name' in request.POST else None
            if name and re.match('^[a-z0-9_-]{3,15}$', name, re.IGNORECASE):
                name = escape(name)
                name_lower_case = name.lower()
                if not User.objects.filter(username__iexact=name).exists():
                    hub_user = User.objects.create_user(name_lower_case, '{0}@unishared.com'.format(name.lower()))
                    hub_user.first_name = name.capitalize() if name.islower() else name

                    hub_user.get_profile().isUniStar = False
                    hub_user.get_profile().is_email_verified = True
                    hub_user.get_profile().enable_notifications = True
                    hub_user.get_profile().about_me = u'This is the place for collaborative note-taking for {0}. Feel free to create documents, or participate, comment, ask questions on the existing ones.'.format(hub_user.first_name)
                    hub_user.get_profile().image = os.path.join('profile_images', 'hub_banner_default.jpg')

                    hub_user.save()
                    hub_user.get_profile().save()

                    Hub.objects.create(user=hub_user, moderator=request.user)

                    hub_url = ProfileHelper.get_profile_url(hub_user.username)
                    context = Context({'profile_url': ProfileHelper.get_profile_url(hub_user.username), 'creator_username': request.user.username})
                    email_task.apply_async(['[{0}] New hub'.format(django_settings.ENV_NAME), context, 'new_hub', None, None, 'gmail'])

                    facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, 'create'), {django_settings.FACEBOOK_OPEN_GRAPH_HUB_TYPE : hub_url}])

                    response = {'success': True, 'message': reverse('website.views.profile', args=[name_lower_case])}
                else:
                    response = {'success': False, 'message': 'Hub already existing'}
            else:
                response = {'success': False, 'message': 'Username is incorrect'}
        else:
            response = {'success': False, 'message': 'User cannot create hub'}

        return HttpResponse(content=json.dumps(response),
            mimetype="application/json", status=200)

@require_http_methods(['GET', 'POST'])
def cowriters_participants_hub(request, role, hub_id):
    """
    List or add cowriters/participants on a hub

    Args:
    role: participant/cowriter
    hub_id: The hub to get/add role
    """
    logger = LoggingHelper.getDebugLogger()
    if hub_id:
        try:
            try:
                id_int = int(hub_id)
                hub_profile = User.objects.get(id=id_int)
            except ValueError:
                hub_profile = User.objects.get(username=hub_id)
        except User.DoesNotExist:
            return HttpResponseNotFound()
    else:
        return HttpResponseBadRequest()

    if hub_profile.get_profile().isUniStar:
        return HttpResponseBadRequest()

    if request.method == 'GET':
        cache_key = '{0}_cowriters'.format(hub_id)

        #role, cowriters = ProfileHelper.get_students_school(hub_profile.get_profile().organization_id, True)

        logger.debug('Looking in the cache for {0}'.format(cache_key))
        response = cache.get(cache_key)

        if not response:
            logger.debug('No cache for {0}'.format(cache_key))
            if hub_profile.get_profile().organization:
                role = hub_profile.get_profile().organization.members_role
            else:
                role = 'participants'

            cowriters = []
            documents = Training.objects.batch_select('cowriters').filter(cowriters=hub_profile, is_deleted=False).distinct()
            for document in documents:
                for cowriter in document.cowriters_all:
                    if cowriter != hub_profile and cowriter not in cowriters:
                        cowriters.append(cowriter)

                if document.creator not in cowriters:
                    cowriters.append(document.creator)

            cowriters_json = []
            for cowriter in cowriters:
                cowriters_json.append(ProfileHelper.get_user_json(cowriter, '90x90'))

            response = {'role' : role, 'cowriters' : cowriters_json}
            cache.set(cache_key, response, 60 * 60)

        return HttpResponse(content=json.dumps(response), mimetype="application/json", status=200)
    elif request.method == 'POST':
        if not request.user.get_profile().can_create:
            return HttpResponse(content=json.dumps({'success': False, 'message' : 'User cannot invite'}), mimetype="application/json")

        # Facebook sharing
        # If user invited people: always publish a story where friends are tagged in
        emails = []
        role_is_cowriter = role == 'cowriters'
        people_facebook_ids = None
        #open_graph_action = 'invite_cowrite' if role_is_cowriter else 'invite_participate'
        open_graph_action = 'cowrite' if role_is_cowriter else 'participate'
        people_facebook_to_mail = []
        if 'people_facebook_ids' in request.POST and request.POST['people_facebook_ids']:
            people_facebook_ids = request.POST['people_facebook_ids']
            people_facebook_ids_split = people_facebook_ids.split(',')
            for people_facebook_id in people_facebook_ids_split:
                if people_facebook_id:
                    logger.debug('Inviting a friend via Facebook : {0}'.format(people_facebook_id))
                    people_facebook_to_mail.append(people_facebook_id)
            emails = emails + list(UserProfile.objects.filter(facebook_id__in=people_facebook_to_mail).select_related().values_list('user__email', flat=True))

            if role_is_cowriter:
                facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, open_graph_action), {django_settings.FACEBOOK_OPEN_GRAPH_HUB_TYPE : ProfileHelper.get_profile_url(hub_profile.username), 'tags' : request.POST['people_facebook_ids']}])
            else:
                facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, open_graph_action), {django_settings.FACEBOOK_OPEN_GRAPH_HUB_TYPE : ProfileHelper.get_profile_url(hub_profile.username), 'tags' : request.POST['people_facebook_ids']}])

        elif request.user.email == hub_profile.email:
            facebook_task.apply_async([request.user, request.user.get_profile().facebook_id, '{0}:{1}'.format(django_settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, 'create'), {django_settings.FACEBOOK_OPEN_GRAPH_HUB_TYPE : ProfileHelper.get_profile_url(hub_profile.username)}])

        # Email sharing
        if 'people_emails' in request.POST and request.POST['people_emails']:
            people_emails = request.POST['people_emails'].split(',')
            people_emails_to_mail = []
            for people_email in people_emails:
                people_email = people_email.strip().lower()
                if email_re.match(people_email):
                    logger.debug('Inviting a friend by email : {0}'.format(people_email))
                    people_emails_to_mail.append(people_email)
                else:
                    logger.debug('Invalid email : {0}'.format(people_email))
            emails = emails + people_emails_to_mail

        if len(emails):
            subject = u'{0} is inviting you to take open notes collaboratively'.format(request.user.first_name)
            context = Context({'first_name' : request.user.first_name, 'hub': {'title': hub_profile.username.capitalize() + '\'s hub', 'url' : ProfileHelper.get_profile_url(hub_profile.username) }, 'ga_campaign_params' : 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=hub_invite_cowriters_email'})

            for email in emails:
                email_task.apply_async([subject, context, 'invite_cowriter_mail', [email]])
        return HttpResponse(content=json.dumps({'success': True, 'message' : '{0} invited'.format(role.capitalize())}), mimetype="application/json")

"""
def stat(request, resource_id):
    View to register a new hint on a resource
    if request.method == 'PUT':
        if resource_id is not None:
            try:
                training_model = Training.objects.get(resource_id=resource_id)

                try:
                    stat_model = StatDocument.objects.get(resource=training_model)
                    stat_model.hits += 1
                    stat_model.save()
                    return HttpResponse(status=200)
                except StatDocument.DoesNotExist:
                    stat_model = StatDocument(resource=training_model, hits=1)
                    stat_model.save()
                    return HttpResponse(status=201)
            except Training.DoesNotExist:
                return HttpResponse(status=404)
    else:
        return HttpResponseBadRequest()
"""

"""
def batch(request):
    #GoogleDriveHelper.batchToStoreDocumentsInDB('/feeds/default/private/full/-/folder?title=UniStars-PRODUCTION&title-exact=true&showfolders=true')
    #GoogleDriveHelper.batchToRenameCollectionWithEnvironmentName()
    return HttpResponse(status=200)
"""
"""
def unistar_wall_100(request):
    unistars_100 = UserProfile.objects.all().values_list('image', flat=True)[593:]
    return render_to_response('unistar_wall.html', {'unistars_100' : unistars_100}, context_instance=RequestContext(request))
"""


def oauth2callback(request):
    if request.user.is_superuser:
        if not xsrfutil.validate_token(django_settings.SECRET_KEY, request.REQUEST['state'],
            request.user):
            return  HttpResponseBadRequest()
        credential = django_settings.FLOW.step2_exchange(request.REQUEST)

        storage = Storage(CredentialsModel, 'id', request.user, 'credential')
        storage.put(credential)

        return HttpResponse()
    else:
        return HttpResponseForbidden()

def oauth2(request):
    if request.user.is_superuser:
        django_settings.FLOW.params['state'] = xsrfutil.generate_token(django_settings.SECRET_KEY,
            request.user)
        django_settings.FLOW.params['access_type'] = 'offline'
        authorize_url = django_settings.FLOW.step1_get_authorize_url()
        return HttpResponseRedirect(authorize_url)
    else:
        return HttpResponseForbidden()