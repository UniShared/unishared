__author__ = 'arnaud'

from django.utils import timezone

class LastSeenMiddleware(object):

    def process_request(self, request):
        user = request.user
        if not user.is_authenticated(): return None
        up = user.get_profile()
        up.last_seen = timezone.now()
        up.last_activity_ip = request.META['REMOTE_ADDR']
        up.save()
        return None