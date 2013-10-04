#!/usr/bin/python
# -*- coding: utf-8 -*-
import calendar
from datetime import timedelta
import time
import random
from urllib2 import HTTPError
from functools import wraps

from celery.signals import worker_ready, task_failure
from django.db.models import Q
from django_facebook.api import get_facebook_graph
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template import Context, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from django.utils.hashcompat import md5_constructor as md5
from celery import task
from dateutil import parser
from gdata.apps.groups.client import GroupsProvisioningClient
from gdata.client import RequestError
from gdata.gauth import OAuthHmacToken, ACCESS_TOKEN
from open_facebook.exceptions import OAuthException, OpenFacebookException, PermissionException
from social_auth.db.django_models import UserSocialAuth
import redis

from UniShared_python.website.helpers.helpers import GoogleDriveHelper, LoggingHelper, MissingConnectionException
from UniShared_python.website.models import TrainingParticipation, TrainingTempShare
from models import Training


__author__ = 'arnaud'

logger = LoggingHelper.getDebugLogger()

REDIS_CLIENT = redis.Redis.from_url(settings.BROKER_URL)
LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes

def only_one(function=None, timeout=LOCK_EXPIRE):
    """Enforce only one celery task at a time."""

    def _dec(run_func):
        """Decorator."""
        @wraps(run_func)
        def _caller(*args, **kwargs):
            """Caller."""
            ret_value = None
            have_lock = False
            args_list = u','.join([unicode(arg) for arg in args])
            key = u"{0}-lock-{1}".format(run_func.__name__, md5(args_list.encode('utf-8')).hexdigest())
            lock = REDIS_CLIENT.lock(key, timeout=timeout)
            try:
                have_lock = lock.acquire(blocking=False)
                if have_lock:
                    ret_value = run_func(*args, **kwargs)
            finally:
                if have_lock:
                    lock.release()

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec

@worker_ready.connect
def at_start(sender, **k):
    if settings.LIVE_DETECTION:
        with sender.app.connection() as conn:
            sender.app.send_task('UniShared_python.website.tasks.live_detection_change_feed', [None], connection=conn)

@task_failure.connect
def live_detection_failure(sender, **k):
    LoggingHelper.getErrorLogger().error('An error occurred in task {0} with args {1}'.format(sender, sender.request.args), exc_info=1)
    if sender is live_detection_change_feed:
        with sender.app.connection() as conn:
            sender.app.send_task('UniShared_python.website.tasks.live_detection_change_feed', sender.request.args, connection=conn)

@task
@only_one
def live_detection_change_feed(last_result):
    logger.debug('Starting live detection with change feed')

    client = GoogleDriveHelper.get_docs_client()

    params = {'includeDeleted' : False}
    if last_result and last_result['startChangeId']:
        logger.debug('Last change id : {0}'.format(last_result['startChangeId']))
        params['startChangeId'] = last_result['startChangeId']

    result = client.changes().list(**params).execute()

    task_result = {'startChangeId' : int(result['largestChangeId']) + 1, 'items' : []}

    for item in result['items']:
        resource_id = item['file']['id']
        updated = parser.parse(item['file']['modifiedDate'])
        title = item['file']['title']

        try:
            last_entries = None
            if last_result:
                last_entries = [last_entry for last_entry in last_result['items'] if last_entry['document_id'] == resource_id]
            last_entry = last_entries[0] if last_entries and len(last_entries) > 0 else None

            document = Training.objects.get(resource_id=resource_id)

            logger.debug('Document recently modified : %s', resource_id)

            if document.title != title:
                logger.debug('Updating title of document {0}'.format(resource_id))
                document.title=title

            updated = calendar.timegm(updated.utctimetuple())
            document.last_updated = updated

            if last_entry:
                logger.debug('Previous entry found')
                logger.debug('Last entry : {0}'.format(last_entry))
                if last_entry['live'] is None:
                    logger.debug('Enabling live in DB for %s', resource_id)

                    document.is_live = True
                    document.is_displayed = True

                    email_task.apply_async(
                        ['Document live', Context({'document_url': GoogleDriveHelper.get_document_url(resource_id)}),
                         'document_live', [a[1] for a in settings.ADMINS], None, 'gmail'])
                else:
                    logger.debug('Document already live %s', resource_id)

                task_result['items'].append({'document_id': resource_id, 'live': True})
            else:
                logger.debug('No previous entry found')
                logger.debug('Creating entry %s', resource_id)
                task_result['items'].append({'document_id': resource_id, 'live': None})

            document.save()
        except Training.DoesNotExist:
            logger.debug('Unexisting resource {0}'.format(resource_id))
        except Exception:
            LoggingHelper.getErrorLogger().error('An error occurred while detecting live', exc_info=1)

    logger.debug('Disabling documents not live anymore')
    Training.objects.filter(~Q(resource_id__in=[item['file']['id'] for item in result['items']]), is_live=True).update(is_live=False)

    logger.debug('Result : %s', task_result)
    live_detection_change_feed.apply_async([task_result], eta=timezone.now()+timedelta(minutes=5))
    return task_result

"""
@task
@only_one
def live_detection_task(last_result):
    logger.debug('Starting live detection')
    trainings = Training.objects.all()[:10].values_list('resource_id', flat=True)

    fiveMinutesBeforeNow = timezone.make_aware(datetime.now() - timedelta(minutes=5), timezone.get_default_timezone())
    logger.debug('Five minutes before now : %s', fiveMinutesBeforeNow)
    result = GoogleDriveHelper._query_resources_batch(trainings)

    task_result = []
    for entry in result['items']:
        logger.debug(entry)
        try:
            resource_id = entry['id']
            if resource_id:
                updated = parser.parse(entry['modifiedDate'])

                last_entries = None
                if last_result:
                    last_entries = [last_entry for last_entry in last_result if last_entry['document_id'] == resource_id]
                last_entry = last_entries[0] if last_entries and len(last_entries) > 0 else None

                if updated > fiveMinutesBeforeNow:
                    logger.debug('Document recently modified : %s', resource_id)

                    if last_entry:
                        logger.debug('Previous entry found')
                        logger.debug('Last entry : {0}'.format(last_entry))
                        if last_entry['live'] is None:
                            logger.debug('Enabling live in DB for %s', resource_id)
                            updated = calendar.timegm(updated.utctimetuple())
                            Training.objects.filter(resource_id=resource_id).update(is_live=True, is_displayed=True, last_updated=updated, title=entry['title'])
                            email_task.apply_async(
                                ['Document live', Context({'document_url': GoogleDriveHelper.get_document_url(resource_id)}),
                                 'document_live', [a[1] for a in settings.ADMINS], None, 'gmail'])
                        else:
                            logger.debug('Document already live %s', resource_id)

                        task_result.append({'document_id': resource_id, 'last_timestamp': entry.updated.text, 'live': True})
                    else:
                        logger.debug('No previous entry found')
                        logger.debug('Creating entry %s', resource_id)
                        task_result.append({'document_id': resource_id, 'last_timestamp': entry.updated.text, 'live': None})
                else:
                    logger.debug('Document not recently modified : %s', resource_id)
                    if last_entry and last_entry['live'] is True:
                        live_detection_task.AsyncResult('live_detection').forget()
                        logger.debug('Disabling live in DB for %s', resource_id)
                        Training.objects.filter(resource_id=resource_id).update(is_live=False)
        except Exception:
            LoggingHelper.getErrorLogger().error('An error occurred while detecting live', exc_info=1)

    logger.debug('Result : %s', task_result)
    live_detection_task.apply_async([task_result], eta=timezone.now()+timedelta(minutes=5))
    return task_result
"""

@task
@only_one
def update_informations_task():
    logger.debug('Starting update informations')

    client = GoogleDriveHelper.get_docs_client()

    params = {}
    params['includeDeleted'] = False

    result = client.changes().list(**params).execute()

    total_updated = 0
    for item in result['items']:
        try:
            resource_id = GoogleDriveHelper.get_id_from_feed_url(item.id.text)
            if resource_id:
                is_updated = False
                title = item['file']['title']
                updated = parser.parse(item['file']['modifiedDate'])
                updated = calendar.timegm(updated.utctimetuple())

                logger.debug('Working on resource {0}'.format(resource_id))

                document = Training.objects.get(resource_id=resource_id)

                if document.last_updated < updated:
                    logger.debug(
                        'Updating last_updated for resource {0} from {1} to {2}'.format(resource_id, document.last_updated,
                            updated))
                    document.last_updated = updated
                    is_updated = True

                if document.title != title:
                    logger.debug(
                        u'Updating title for resource {0} from {1} to {2}'.format(resource_id, document.title, title))
                    document.title = title
                    is_updated = True

                if is_updated:
                    total_updated += 1
                    document.save()
        except Training.DoesNotExist:
            logger.debug('Unexisting resource {0}'.format(resource_id))
        except Exception:
            LoggingHelper.getErrorLogger().error('An error occured while updating {0}'.format(item.id.text),
                exc_info=1)

    logger.debug('{0} resources updated'.format(total_updated))

@task
@only_one
def email_task(subject, context, template, to, bcc=None, connection_label=None):
    if not to and not bcc:
        logger.debug('No recipients, adding managers')
        to = [a[1] for a in settings.MANAGERS]
        connection_label = 'gmail'

    logger.debug('Starting email task (subject: %s, template: %s, context: %s to: %s, bcc: %s, connection_label: %s',
        subject, template, context, to, bcc, connection_label)

    def filter_emails(emails):
        filtered_emails = []

        if emails:
            for email in emails:
                try:
                    user_profile = User.objects.get(email=email).get_profile()

                    if user_profile.is_email_verified is True and user_profile.enable_notifications is True:
                        filtered_emails.append(email)
                except User.DoesNotExist:
                    filtered_emails.append(email)
        return filtered_emails

    filtered_to = filter_emails(to)
    filtered_bcc = filter_emails(bcc)

    logger.debug('To length after filtering: %s', len(filtered_to))
    logger.debug('Bcc length after filtering: %s', len(filtered_bcc))

    if len(filtered_to) or len(filtered_bcc):
        if connection_label is None:
            connection_label = getattr(settings, 'EMAIL_CONNECTION_DEFAULT', None)

        try:
            connections = getattr(settings, 'EMAIL_CONNECTIONS')
            real_options = connections[connection_label]
            admin_options = connections['gmail']
        except KeyError, AttributeError:
            raise MissingConnectionException(
                'Settings for connection "%s" were not found' % connection_label)

        context.update({'BASE_URL': settings.BASE_URL,
                        'link_underlined': 'border-bottom: 1px dashed #848484;text-decoration: none;',
                        'link_style_share': 'color: #3CBDEE;border-bottom: 1px dashed #3CBDEE;text-decoration: none;',
                        'link_style_participate': 'color: #F18C1B;text-decoration: none;border-bottom: 1px dashed #F18C1B;'})
        text_message = get_template('mails/{0}.txt'.format(template)).render(context)

        real_connection = get_connection(**real_options)
        real_connection.open()

        admin_connection = get_connection(**admin_options)
        admin_connection.open()

        from_email = u'"Clément from UniShared" <clement@unishared.com>'
        real_email = EmailMultiAlternatives(subject, text_message, from_email,
            filtered_to, filtered_bcc, real_connection)
        admin_email = EmailMultiAlternatives(subject, text_message, from_email,
            [a[1] for a in settings.ADMINS], None, admin_connection)
        try:
            html_message = get_template('mails/{0}.html'.format(template)).render(context)
            real_email.attach_alternative(html_message, 'text/html')
            admin_email.attach_alternative(html_message, 'text/html')
        except TemplateDoesNotExist:
            pass

        real_email.send(fail_silently=False)
        admin_email.send(fail_silently=False)

        real_connection.close()
        admin_connection.close()

@task
@only_one
def activation_emails_task():
    logger.debug('Starting activation emails task')
    users = User.objects.all().select_related('profile')

    for user in users:
        try:
            if user.date_joined and user.last_login:
                users_has_documents = Training.objects.filter(creator_id=user).exists()
                context = Context({'user': user})

                today_at_midnight = timezone.now().replace(hour=0, minute=0, second=0)
                logger.debug(user.date_joined)

                if timezone.is_aware(user.date_joined):
                    date_joined = user.date_joined
                else:
                    date_joined = timezone.make_aware(user.date_joined, timezone.get_current_timezone())

                days_since_signup = (today_at_midnight - date_joined).days
                if days_since_signup == 2 and not users_has_documents:
                    logger.debug('Sending activation email to {0}'.format(user.email))
                    context.update({
                    'ga_campaign_params': 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=activation_mail'})
                    email_task.apply_async(
                        [u'Create your first collaborative document', context, 'activation_mail', [user.email]])

                if user.get_profile().last_seen:
                    days_since_login = (today_at_midnight - user.get_profile().last_seen).days
                    if days_since_login == 14:
                        logger.debug('Sending dropping out email to {0}'.format(user.email))
                        context.update({
                        'ga_campaign_params': 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=dropping_out_mail'})
                        email_task.apply_async([u'Dropping out?', context, 'dropping_out_mail', [user.email]])
        except:
            LoggingHelper.getErrorLogger().error('An error occurred while sending activation email to user {0}'.format(user.id),
                exc_info=1)


@task
@only_one
def facebook_friends_joined_task():
    logger.debug('Starting Facebook friends joined task')
    users = User.objects.all()

    for user in users:
        try:
            logger.debug('Querying Facebook friends')
            user_social = UserSocialAuth.objects.get(user=user, provider='facebook')
            access_token = user_social.extra_data['access_token']

            graph = get_facebook_graph(access_token=access_token)
            friends_using_app = None
            try:
                friends_using_app = graph.get('{0}/friends'.format(user_social.uid), fields='installed')['data']
            except OAuthException:
                user_social.refresh_token()

            if friends_using_app:
                logger.debug('Friends using apps: %s',
                    [friend_using_app['id'] for friend_using_app in friends_using_app if
                     'installed' in friend_using_app])
                last_day = timezone.now().replace(hour=0, minute=0, second=0) - timedelta(days=1)
                friends_profile = UserSocialAuth.objects.filter(
                    uid__in=[friend_using_app['id'] for friend_using_app in friends_using_app if
                             'installed' in friend_using_app], user__date_joined__gt=last_day).select_related('user')

                friends_profile_count = len(friends_profile)
                if friends_profile_count:
                    logger.debug('Sending Facebook friends joined email to {0}'.format(user.email))
                    context = Context({'first_name': user.first_name, 'friends_profile': friends_profile,
                                       'ga_campaign_params': 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=fb_friends_joined'})

                    if friends_profile_count == 1:
                        subject_start = u'Your friend '
                        subject_end = u' takes notes collaboratively'
                    else:
                        subject_start = u'Your friends '
                        subject_end = u' take notes collaboratively'
                    email_task.apply_async([subject_start + u','.join(
                        [friend_profile.user.first_name for friend_profile in friends_profile[:3]]) + subject_end,
                                            context, 'facebook_friends_joined', [user.email]])
        except UserSocialAuth.DoesNotExist:
            logger.debug('No access token')
        except HTTPError:
            logger.debug('HTTP Error while checking friends who have joined',
                exc_info=1)


@task
@only_one
def google_apps_add_group_task(group_id, member_id):
    logger.debug('Starting Google Apps add to group task')
    try:
        logger.debug('Get GroupsProvisioningClient')
        clientInstance = GroupsProvisioningClient('unishared.com',
            OAuthHmacToken('unishared.com', '',
                '', '', ACCESS_TOKEN))
        clientInstance.ssl = True
        logger.debug('Add {0} to {1}'.format(member_id, group_id))
        clientInstance.AddMemberToGroup(group_id, member_id)
        return True
    except RequestError:
        LoggingHelper.getErrorLogger().debug("Request error while adding user to Google group", exc_info=1)
        return False
    except Exception:
        LoggingHelper.getErrorLogger().error("Error while adding user to Google group", exc_info=1)
        return False


@task
@only_one
def facebook_task(user, facebook_id, action, params):
    try:
        user_social = UserSocialAuth.objects.get(user=user, provider='facebook')
        access_token = user_social.extra_data['access_token']
        graph = get_facebook_graph(access_token=access_token)
        if graph:
            for n in range(0, 5):
                try:
                    url = None
                    try:
                        if u'class' in params:
                            url = params[u'class']
                        elif u'link' in params:
                            url = params[u'link']
                        if url:
                            graph.set(u'/', {'ids': url, 'scrape': 'true'})
                    except OAuthException:
                        LoggingHelper.getDebugLogger().debug(u'Error while scraping {0}'.format(url), exc_info=1)
                    return graph.set(u'{0}/{1}'.format(facebook_id, action), params)
                except PermissionException:
                    LoggingHelper.getDebugLogger().debug(
                        u'Permission not granted (facebook_id : {0}, action {1}, params {2})'.format(facebook_id,
                            action, params), exc_info=1)
                except OAuthException:
                    LoggingHelper.getDebugLogger().debug(
                        u'Refreshing token (facebook_id : {0}, action {1}, params {2})'.format(facebook_id, action,
                            params), exc_info=1)
                    try:
                        user_social.refresh_token()
                    except Exception:
                        pass
                except OpenFacebookException:
                    LoggingHelper.getErrorLogger().error(
                        u'Error while posting on Facebook (facebook_id : {0}, action {1}, params {2})'.format(
                            facebook_id, action, params), exc_info=1)
                    time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))

                    if action in ['{0}:invite_participate'.format(settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME), '{0}:invite_cowrite'.format(settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME)]:
                        facebook_task.apply_async([user, facebook_id, '{0}:{1}'.format(settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, 'cowrite'), params])
                        break

    except UserSocialAuth.DoesNotExist:
        LoggingHelper.getDebugLogger().debug('No access token')


@task
@only_one
def document_temp_share_task(document, user):
    logger.debug(u'Looking for a temporary share for training {0} and user {1}'.format(document.resource_id, user))

    trainingTempShares = TrainingTempShare.objects.filter(
        Q(user_invited=user) | Q(facebook_id=user.get_profile().facebook_id) | Q(email=user.email), training=document)

    if trainingTempShares.exists():
        logger.debug(u'Temporary share found for training {0} and user {1}'.format(document.resource_id, user))
        for trainingTempShare in trainingTempShares:
            if trainingTempShare.role == 'cowriters':
                if document.creator != user and user not in document.cowriters.all():
                    logger.debug(u'Adding co-writer for training {0} and user {1}'.format(document.resource_id, user))
                    document.cowriters.add(user)

                    if user in document.participants.all():
                        logger.debug(u'Remove participant for training {0} and user {1}'.format(document.resource_id, user))
                        document.participants.remove(user)
                    document.save()
                else:
                    logger.debug(u'User {0} is already cowriter on training {1}'.format(user, document.resource_id))
            elif trainingTempShare.role == 'participants':
                if document.creator != user and user not in document.participants.all() and user not in document.cowriters.all():
                    logger.debug(u'Adding participant for training {0} and user {1}'.format(document.resource_id, user))
                    document.participants.add(user)
                    document.save()
                else:
                    logger.debug(u'User {0} is already cowriter/participant on training {1}'.format(user, document.resource_id))
            trainingTempShare.delete()
    else:
        if document.creator != user and user not in document.cowriters.all() and user not in document.participants.all():
            logger.debug('Adding participant for training {0} and user {1}'.format(document.resource_id, user))
            document.participants.add(user)

            if Training.objects.filter(participants=user).count() == 1:
                logger.debug('Sending first participation mail')
                context = Context({'user': user,
                                   'document': {'url': GoogleDriveHelper.get_document_url(document.resource_id),
                                   'title': document.title},
                                   'ga_campaign_params': 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=new_document_participation_mail'})
                email_task.apply_async(
                    ["Yihaa, you participated in a collaborative document!", context, "new_document_participation_mail",
                     [user.email]])

        document.total_views += 1
        document.total_views_open25 += 1
        document.save()

        try:
            logger.debug('Adding participation for training {0} and user {1}'.format(document.resource_id, user))
            participation = TrainingParticipation.objects.get(user=user, training=document)
            participation.count += 1
            participation.save()
        except TrainingParticipation.DoesNotExist:
            TrainingParticipation.objects.create(user=user, training=document, count=1)

@task
@only_one
def acl_feed_task(email, resource_id, with_group=True):
    if with_group:
        logger.debug('Adding writing permission to anyone')
        GoogleDriveHelper.share_to(resource_id, emails=['{0}@unishared.com'.format(settings.GAPPS_GROUP_NAME), email], with_default_entry=True)
    else:
        logger.debug('Adding writing permission to {0}'.format(email))
        GoogleDriveHelper.share_to(resource_id, emails=[email])

@task
def move_document_to_user_folder(resource_id, user):
    logger = LoggingHelper.getDebugLogger()
    client = GoogleDriveHelper.get_docs_client()

    dest_folder = user.get_profile().drive_folder_id
    if not dest_folder:
        logger.debug('Creating folder for {0}'.format(user.username))
        dest_folder = GoogleDriveHelper.create_unistar_folder(user)
        user.get_profile().drive_folder_id = dest_folder
        user.get_profile().save()

    logger.debug('Moving {0} to {1}'.format(resource_id, GoogleDriveHelper._get_unistar_collection_name(user.username)))
    client.files().update(fileId=resource_id, body={"parents":[{'id':dest_folder}]}).execute()
