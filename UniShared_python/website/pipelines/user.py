from datetime import datetime, timedelta
import hashlib
from urllib2 import urlopen

from django.core.files.base import ContentFile
from django.template.context import Context
from django.template.defaultfilters import slugify
from social_auth.backends import USERNAME
from social_auth.backends.facebook import FacebookBackend

from UniShared_python.settings import GAPPS_GROUP_NAME
from UniShared_python.website.tasks import email_task, google_apps_add_group_task


def get_user_avatar(backend, details, response, social_user, uid, user, *args, **kwargs):
    url = None
    if backend.__class__ == FacebookBackend:
        url = "http://graph.facebook.com/%s/picture?type=large" % response['id']
    
    if url:
        profile = user.get_profile()
        if profile.image == '':
            avatar = urlopen(url)       

            content = avatar.read()
            md5 = hashlib.md5()
            md5.update(content)
            name = '{0}-{1}.jpg'.format(slugify(user.username + " social"), md5.hexdigest()[:12])
            profile.image.save(name, ContentFile(content))
            profile.save()

def add_user_to_group(backend, details, response, user, is_new=False, *args, **kwargs):   
    """ 
    Add current user to the UniShared's Google Group
    """
    
    if is_new:
        google_apps_add_group_task.apply_async([GAPPS_GROUP_NAME, user.email])

def send_welcome_mail(backend, details, response, user, is_new=False, *args, **kwargs):
    """
    Send a welcome mail
    """

    if is_new:
        context = Context({'user': user, 'ga_campaign_params' : 'utm_source=unishared&utm_content=v1&utm_medium=e-mail&utm_campaign=welcome_mail'})

        email_task.apply_async([u'Welcome on UniShared!', context, 'welcome_mail', [user.email]], eta= datetime.utcnow() + timedelta(hours=1))

def update_user_details(backend, details, response, user, is_new=False, *args,
                        **kwargs):
    user_profile = user.get_profile()

    if user_profile.facebook_id is None:
        user_profile.facebook_id = response.get('id')

    if not user_profile.is_organization_verified and response.get('education') is not None :
        kwargs['request'].session['education'] = response.get('education')

    if is_new:
        for name, value in details.iteritems():
            # do not update username, it was already generated
            if name in (USERNAME, 'id', 'pk'):
                continue
            if value and value != getattr(user, name, None):
                setattr(user, name, value)

        about_me = response.get('bio')
        if about_me is not None:
            if user_profile.about_me == '':
                user_profile.about_me = about_me

        user_profile.facebook_profile_url = response.get('link')
        user_profile.isUniStar = True

    user_profile.save()
    user.save()