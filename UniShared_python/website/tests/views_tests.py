'''
Created on 27 juil. 2012

@author: Arnaud
'''
import json
import time
import apiclient
from apiclient.http import RequestMockBuilder

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch, Mock
from social_auth.db.django_models import UserSocialAuth

from website.helpers.helpers import GoogleDriveHelper, LoggingHelper
from website.models import Training, TrainingTempShare, NoteTakingBuddy


class HomeViewTest(TestCase):
    def test_correct_template(self):
        response = self.client.get('/')
        
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'index.html')
        
class QrCodeViewTest(TestCase):
    def test_redirect_checkthis(self):
        response = self.client.get('/qrcode/')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response._headers['location'][1], 'http://checkthis.com/mdtj', 'Not the correct location')

class PolicyViewTest(TestCase):
    def test_correct_template(self):
        response = self.client.get('/policy/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'privacy-policy.html')
        
class TwitterCompleteViewTest(TestCase):
    def test_correct_template(self):
        response = self.client.get('/social/login/twitter-complete/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'registration/twitter_complete.html')
        
class PartnersViewTest(TestCase):
    def test_correct_template(self):
        response = self.client.get('/partners/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'partners.html')

class YYprodViewTest(TestCase):
    def test_correct_template(self):
        response = self.client.get('/yyprod/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'yyprod.html')

class LoginErrorViewTest(TestCase):
    def test_correct_template(self):
        response = self.client.get('/login-error/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'registration/login_error.html')

class ViewTestWithoutFBLogin(TestCase):
    def setUp(self):
        settings.AUTHENTICATION_BACKENDS = (
            'django.contrib.auth.backends.ModelBackend',
        )
        settings.PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.MD5PasswordHasher',
        )
        
        self.user = User.objects.create_user('test-user', 'test-user@unishared.com', 'test')
        self.social_auth_user = UserSocialAuth.objects.create(user=self.user, provider='facebook', extra_data={'access_token' : '1234567890'})
        
class ProfileViewTest(ViewTestWithoutFBLogin):
    def setUp(self):
        super(ProfileViewTest, self).setUp()
        self.assertTrue(self.client.login(username='test-user', password='test'), "Login failed")
        response = self.client.get('/profile/')
        self.assertRedirects(response, '/login/')
        
    def test_post_login_student(self):
        response = self.client.post('/login/', {'is_student' : 'true', 'school' : 'test school', 'email' : 'test-user-updated@unishared.com'})
        
        self.assertTrue(response.status_code, 200)
        
        response_dict = json.loads(response.content)
        
        self.assertTrue(response_dict['success'], 'Error on update profile')
        self.assertTrue(response_dict['is_student']['success'], 'Error on update is_student')
        self.assertTrue(response_dict['school']['success'], 'Error on update school')
        self.assertTrue(response_dict['email']['success'], 'Error on update email')
        
        user = User.objects.get(username='test-user')
        user_profile = user.get_profile()
        self.assertTrue(user_profile.is_student, 'Not the correct is student status')
        self.assertEqual(user_profile.organization.name, 'test school', 'Not the correct organization')
        self.assertTrue(user_profile.is_organization_verified, 'Organization not verified')
        self.assertEqual(user.email, 'test-user-updated@unishared.com', 'Not the correct email')
        self.assertTrue(user_profile.is_email_verified, 'Email not verified')
        
    def test_post_login_student_not_gmail(self):
        response = self.client.post('/login/', {'is_student' : 'true', 'school' : 'test school', 'email' : 'test-user-updated@notagappsdomain.com'})
        
        self.assertTrue(response.status_code, 200)
        response_dict = json.loads(response.content)
        
        self.assertFalse(response_dict['success'], 'Error on update profile')
        self.assertTrue(response_dict['is_student']['success'], 'Error on update is_student')
        self.assertTrue(response_dict['school']['success'], 'Error on update school')
        self.assertFalse(response_dict['email']['success'], 'Error on update email')
        self.assertEqual(response_dict['email']['message'], 'Please provide a valid gmail address', 'Not the correct message on update email')
        
        user = User.objects.get(username='test-user')
        user_profile = user.get_profile()
        self.assertTrue(user_profile.is_student, 'Not the correct is student status')
        self.assertEqual(user_profile.organization.name, 'test school', 'Not the correct organization')
        self.assertTrue(user_profile.is_organization_verified, 'Organization not verified')
        self.assertNotEqual(user.email, 'test-user-updated@notagappsdomain.com', 'Email has been updated')
        self.assertFalse(user_profile.is_email_verified, 'Email verified')
        
    def test_post_login_lifelonglearner(self):
        response = self.client.post('/login/', {'is_student' : 'false', 'email' : 'test-user-updated@unishared.com'})
        
        self.assertTrue(response.status_code, 200)
        response_dict = json.loads(response.content)
        
        self.assertTrue(response_dict['success'], 'Error on update profile')
        self.assertTrue(response_dict['is_student']['success'], 'Error on update is_student')
        self.assertTrue(response_dict['email']['success'], 'Error on update email')
        
        user = User.objects.get(username='test-user')
        user_profile = user.get_profile()
        self.assertFalse(user_profile.is_student, 'Not the correct is student status')
        self.assertFalse(user_profile.is_organization_verified, 'Not the correct organization')
        self.assertEqual(user.email, 'test-user-updated@unishared.com', 'Not the correct email')
        self.assertTrue(user_profile.is_email_verified, 'Email not verified')
        
    def test_post_login_lifelonglearner_not_gmail(self):
        response = self.client.post('/login/', {'is_student' : 'false', 'email' : 'test-user-updated@notagappsdomain.com'})
        
        self.assertTrue(response.status_code, 200)
        response_dict = json.loads(response.content)
        
        self.assertTrue(response_dict['success'], 'Error on update profile')
        self.assertTrue(response_dict['is_student']['success'], 'Error on update is_student')
        self.assertTrue(response_dict['email']['success'], 'Error on update email')
        
        user = User.objects.get(username='test-user')
        user_profile = user.get_profile()
        self.assertFalse(user_profile.is_student, 'Not the correct is student status')
        self.assertFalse(user_profile.is_organization_verified, 'Organization verified')
        self.assertEqual(user.email, 'test-user-updated@notagappsdomain.com', 'Email has not been updated')
        self.assertTrue(user_profile.is_email_verified, 'Email not verified')
        
class CreateClassViewTest(ViewTestWithoutFBLogin):
    def setUp(self):
        super(CreateClassViewTest, self).setUp()
        self.training = Training.objects.create(resource_id='12345', title='test', last_updated=time.time(), creator_id=self.user.id)
        self.assertTrue(self.client.login(username='test-user', password='test'), "Login failed")
        
    @patch.object(GoogleDriveHelper, 'create_new_document')
    def test_post_class(self, mock_create_document):
        mock_create_document.return_value = self.training
        
        response = self.client.post('/notes/create/', {'class_title' : 'test'})

        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.content)
        
        self.assertTrue(u'resource_id' in response_dict, "No resource_id returned")
        self.assertEqual(response_dict['resource_id'], '12345', "Wrong resource id returned")
    
    @patch('website.helpers.threads.TrainingTempShareThread')
    def test_get_class(self, mock_trainingtempsharethread):
        response = self.client.get('/notes/{0}'.format(self.training.resource_id))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_new_design.html')
        self.assertTemplateUsed(response, 'class/document.html')
        
    @patch('website.helpers.threads.FacebookActionThread')
    def test_add_cowriters_facebook(self, mock_fb_actionthread):
        facebook_id = '12345'
        response = self.client.post('/notes/cowriters/{0}'.format(self.training.resource_id), {'cowriters_facebook_ids' : facebook_id})
        
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.content)
        
        self.assertTrue('message' in response_dict, "Co-writers invitation failed")
        self.assertEqual(response_dict['message'], 'Co-writers invited', 'Not the right message')
        
        try:
            TrainingTempShare.objects.get(training=self.training, facebook_id=facebook_id)
        except TrainingTempShare.DoesNotExist:
            self.fail('No training temp share created')

class NoteTakingBuddyViewTest(ViewTestWithoutFBLogin):
    def setUp(self):
        super(NoteTakingBuddyViewTest, self).setUp()
        self.assertTrue(self.client.login(username='test-user', password='test'), "Login failed")

    def test_register_new_buddy(self):
        passionated_by_subject = 'true'
        note_taking_format = NoteTakingBuddy.BULLET_POINTS
        augmented_documents = 'true'
        behaviour = NoteTakingBuddy.WRITE_MOST_NOTES
        live_session = 'true'
        score = 2 # 2 points for augmented documents and live session

        response = self.client.post(reverse('website.views.note_taking_buddy'),
            {'id_passionated_by_subject' : passionated_by_subject, 'id_note_taking_format': note_taking_format, 'id_augmented_documents': augmented_documents,
             'id_behaviour': behaviour, 'id_live_session': live_session})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(NoteTakingBuddy.objects.filter(user=self.user, passionated_by_subject=passionated_by_subject, note_taking_format=note_taking_format,
            augmented_documents=augmented_documents, behaviour=behaviour, live_session=live_session, score=score).exists())

        self.assertTemplateUsed(response, 'note_taking_buddy_results.html')

class ActivityViewTest(TestCase):
    def setUp(self):
        super(ActivityViewTest, self).setUp()

        self.logger = LoggingHelper.getDebugLogger()

        response = {
            'items': [
                {
                    'id':'abcdef'
                },
                {
                    'id':'1234'
                }
            ]
        }
        requestBuilder = RequestMockBuilder(
            {
                'drive.files.list': (None, json.dumps(response)),
            }
        )

        GoogleDriveHelper.get_docs_client = Mock()
        GoogleDriveHelper.get_docs_client.return_value = apiclient.discovery.build("drive", "v2", requestBuilder=requestBuilder)

    def test_all_search_no_result(self):
        response = self.client.get('/activity/all/documents', {'q' : 'toto'})
        self.logger.debug(response.content)
        self.assertEqual(json.loads(response.content)['totalRecords'], 0)

    def test_all_search_one_result(self):
        creator = User.objects.create_user('test-user')
        document = Training.objects.create(resource_id='abcdef', title='Test', creator=creator, is_displayed=True, is_deleted=False)
        self.assertEqual(Training.objects.all().count(), 1)

        response = self.client.get('/activity/all/documents', {'q' : 'toto'})
        self.logger.debug(response.content)
        self.assertEqual(json.loads(response.content)['totalRecords'], 1)

        document.delete()
        creator.delete()

    def test_all_search_multiple_results(self):
        creator = User.objects.create_user('test-user')

        document1 = Training.objects.create(resource_id='abcdef', title='Test', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='1234', title='Test', creator=creator, is_displayed=True, is_deleted=False)
        self.assertEqual(Training.objects.all().count(), 2)

        response = self.client.get('/activity/all/documents', {'q' : 'toto'})
        self.logger.debug(response.content)
        self.assertEqual(json.loads(response.content)['totalRecords'], 2)

        document2.delete()
        document1.delete()
        creator.delete()



