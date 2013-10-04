from django.contrib.auth.models import User
from django.utils import unittest
from mock import patch
from social_auth.db.django_models import UserSocialAuth
from website.helpers.threads import FacebookThread
import urllib2

class FacebookThreadTest(unittest.TestCase):
    def setUp(self):
        self.facebook_id = '100004426234084'
        self.u1 = User.objects.create(username='facebookthreadtestuser')
        self.up1 = self.u1.get_profile()
        self.up1.facebook_id = self.facebook_id
        self.usa1 = UserSocialAuth.objects.create(user=self.u1, provider='facebook', uid=self.facebook_id)
        self.usa1.extra_data['access_token'] = 'AAABbIanCCvEBAICx6RBfdl8RzE3hJ41agqhWolmDvGfAZAZB7qtcfx2Bp5Tx1a8t3jDDsqltIVBTeIiqwvZArJZA044ZAJQ2y0ddXbQC3rAZDZD'
        self.usa1.save()

    def tearDown(self):
        self.up1.delete()
        self.usa1.delete()
        self.u1.delete()
        
    @patch('urllib2.urlopen')
    def testRefreshToken(self, mock_url_open):
        assert urllib2.urlopen is mock_url_open
        mock_url_open.return_value = "{'access_token' : 'fake_access_token', 'expires': 'fake_expires'}"
        fb_thread = FacebookThread(self.up1, self.facebook_id, None, None)
        
        fb_thread.refresh_token()
        self.assertIsNotNone(self.usa1.extra_data['access_token'], 'Extra data is empty after refresh')
