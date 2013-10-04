from UniShared_python.settings import GAPPS_GROUP_NAME
from UniShared_python.website.models import Training
from UniShared_python.website.helpers.helpers import GoogleDriveHelper
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from gdata.client import RequestError
from gdata.gauth import OAuthHmacToken, ACCESS_TOKEN
from gdata.docs.data import AclEntry
from gdata.acl.data import AclScope, AclRole
from optparse import make_option

class Command(BaseCommand):
    help = 'Remove documents editors and add Google groups'

    def handle(self, *args, **options):
        self.stdout.write('Executing Remove Docs editors to group command\n')
                 
        client = GoogleDriveHelper.get_docs_client()

        trainings = Training.objects.all()
        for training in trainings:
            try:
                self.stdout.write('Entry : {0}\n'.format(training.resource_id))
                entry = client.GetResourceById(training.resource_id)
                acl_feed = client.GetResourceAcl(entry)
                    
                if acl_feed:
                    for acl in acl_feed.entry:
                        if acl.scope.type == 'user' and acl.role.value != 'owner':
                            self.stdout.write('Remove ACL entry : {0}\n'.format(acl.scope.value))
                            client.DeleteAclEntry(acl)
                    
                    group_mail = '{0}@unishared.com'.format(GAPPS_GROUP_NAME)
                    self.stdout.write('Add {0} as editor\n'.format(group_mail))
                    acl_entry_user = AclEntry(
                        scope=AclScope(value=group_mail, type='user'),
                        role=AclRole(value='writer'))
                    client.AddAclEntry(entry, acl_entry_user, send_notifications=False)
                    
                    self.stdout.write('Add {0} as editor\n'.format(training.creator.email))
                    acl_entry_user = AclEntry(
                        scope=AclScope(value=training.creator.email, type='user'),
                        role=AclRole(value='writer'))
                    client.AddAclEntry(entry, acl_entry_user, send_notifications=False)
            except Exception, e:
                print e