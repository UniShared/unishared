from django.core.management.base import BaseCommand, CommandError
from optparse import make_option 
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete user\'s session'),
        )
    args = '<user_id user_id ...>'
    help = 'Retrieve session key for user_ids'

    def handle(self, *args, **options):
        self.stdout.write('Executing get session from user command\n')
        sessions = Session.objects.all()
        
        for session in sessions:
            user_id_session = session.get_decoded().get('_auth_user_id')
            
            for user_id in args:                
                if user_id_session == int(user_id):
                    self.stdout.write('{0} : {1}\n'.format(args[0], session.session_key))
                    if options['delete']:
                        session.delete()
            