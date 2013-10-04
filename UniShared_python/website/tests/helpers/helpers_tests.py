'''
Created on Dec 7, 2012

@author: arnaud
'''
import json
import apiclient
from apiclient.http import RequestMockBuilder
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import unittest
from mock import Mock

from UniShared_python.website.helpers.helpers import ProfileHelper, GoogleDriveHelper, LoggingHelper
from website.models import Training


class ProfileHelperTest(unittest.TestCase):
    def testIsGmail_with_gmail_adress(self):
        self.assertTrue(ProfileHelper.is_gmail('arnaud.breton91@gmail.com'), 'DNS test is not working')
        
    def testIsGmail_with_gapps_adress(self):
        self.assertTrue(ProfileHelper.is_gmail('arnaud@unishared.com'), 'DNS test is not working')
        
    def testIsGmail_with_not_google_adress(self):
        self.assertFalse(ProfileHelper.is_gmail('arnoo91@free.fr'), 'DNS test is not working')

class GoogleDriveHelperTest(unittest.TestCase):
    def setUp(self):
        super(GoogleDriveHelperTest, self).setUp()

        self.logger = LoggingHelper.getDebugLogger()

    def tearDown(self):
        super(GoogleDriveHelperTest, self).tearDown()

        Training.objects.all().delete()
        User.objects.all().delete()

    def test_get_document_url(self):
        resource_id = 'toto'
        url_expected = '{0}{1}'.format(settings.BASE_URL, reverse('website.views.embedded_document', args=[resource_id]))

        self.assertEqual(GoogleDriveHelper.get_document_url(resource_id), url_expected)

    def test_get_unistar_collection_name(self):
        username = 'toto'
        folder_name = GoogleDriveHelper._get_unistar_collection_name(username)

        self.assertEqual(folder_name, '[UniShared-{0}] {1}'.format(settings.ENV_NAME, username))

    def test_create_unistar_folder(self):
        response = {
            'id' : 'abcdef'
        }

        requestBuilder = RequestMockBuilder(
            {
                'drive.files.insert': (None, json.dumps(response)),
            }
        )

        GoogleDriveHelper.get_docs_client = Mock()
        GoogleDriveHelper.get_docs_client.return_value = apiclient.discovery.build("drive", "v2", requestBuilder=requestBuilder)

        user = User.objects.create_user('arnaud.breton','test@unishared.com')
        self.assertEqual(GoogleDriveHelper.create_unistar_folder(user), 'abcdef')

    def test_search_documents(self):
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

        creator = User.objects.create_user('test-user')
        Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        Training.objects.create(resource_id='resource_id_test2', title='tata', creator=creator, is_displayed=True, is_deleted=False)

        search_results = GoogleDriveHelper.search_documents('toto')

        self.assertGreater(len(search_results), 0)
        self.assertIn('abcdef', search_results)
        self.assertIn('1234', search_results)
        self.assertIn('resource_id_test', search_results)
        self.assertNotIn('resource_id_test2', search_results)

    def test_search_documents_title_only(self):
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

        creator = User.objects.create_user('test-user')
        Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        search_results = GoogleDriveHelper.search_documents('toto', title_only=True)

        self.assertGreater(len(search_results), 0)
        self.assertNotIn('abcdef', search_results)
        self.assertNotIn('1234', search_results)
        self.assertIn('resource_id_test', search_results)

        self.assertEqual(GoogleDriveHelper.get_docs_client.call_count, 0)

    def test_get_documents(self):
        creator = User.objects.create_user('test-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        results = GoogleDriveHelper.get_documents([document, document2, document3])

        self.assertIn(document, results)
        self.assertIn(document2, results)
        self.assertIn(document3, results)

    def test_get_documents_max_documents(self):
        creator = User.objects.create_user('test-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        results = GoogleDriveHelper.get_documents([document, document2, document3], max_documents=1)

        self.assertIn(document, results)
        self.assertNotIn(document2, results)
        self.assertNotIn(document3, results)

    def test_get_documents_max_documents_second_page(self):
        creator = User.objects.create_user('test-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        results = GoogleDriveHelper.get_documents([document, document2, document3], max_documents=1, id_page=2)

        self.assertNotIn(document, results)
        self.assertIn(document2, results)
        self.assertNotIn(document3, results)

    def test_get_all_user_documents(self):
        creator = User.objects.create_user('test-user')
        other_user = User.objects.create_user('other-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=other_user, is_displayed=True, is_deleted=False)

        total_records, results = GoogleDriveHelper.get_all_user_documents(creator)

        self.assertEqual(total_records, 1)
        self.assertIn(document, results)
        self.assertNotIn(document2, results)

    def test_get_all_user_documents_max_documents(self):
        creator = User.objects.create_user('test-user')
        other_user = User.objects.create_user('other-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=other_user, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        total_records, results = GoogleDriveHelper.get_all_user_documents(creator, max_documents=1)

        self.assertEqual(total_records, 2)
        self.assertIn(document, results)
        self.assertNotIn(document2, results)
        self.assertNotIn(document3, results)

    def test_get_all_user_documents_max_documents_second_page(self):
        creator = User.objects.create_user('test-user')
        other_user = User.objects.create_user('other-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=other_user, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        total_records, results = GoogleDriveHelper.get_all_user_documents(creator, max_documents=1, id_page=2)

        self.assertEqual(total_records, 2)
        self.assertNotIn(document, results)
        self.assertNotIn(document2, results)
        self.assertIn(document3, results)

    def test_get_all_documents(self):
        creator = User.objects.create_user('test-user')
        other_user = User.objects.create_user('other-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=other_user, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        total_records, results = GoogleDriveHelper.get_all_documents()

        self.assertEqual(total_records, 3)
        self.assertIn(document, results)
        self.assertIn(document2, results)
        self.assertIn(document3, results)

    def test_get_all_documents_max_documents(self):
        creator = User.objects.create_user('test-user')
        other_user = User.objects.create_user('other-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=other_user, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        total_records, results = GoogleDriveHelper.get_all_documents(max_documents=1)

        self.assertEqual(total_records, 3)
        self.assertIn(document, results)
        self.assertNotIn(document2, results)
        self.assertNotIn(document3, results)

    def test_get_all_documents_max_documents_second_page(self):
        creator = User.objects.create_user('test-user')
        other_user = User.objects.create_user('other-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', creator=creator, is_displayed=True, is_deleted=False)
        document2 = Training.objects.create(resource_id='resource_id_test2', title='toto', creator=other_user, is_displayed=True, is_deleted=False)
        document3 = Training.objects.create(resource_id='resource_id_test3', title='toto', creator=creator, is_displayed=True, is_deleted=False)

        total_records, results = GoogleDriveHelper.get_all_documents(max_documents=1, id_page=2)

        self.assertEqual(total_records, 3)
        self.assertNotIn(document, results)
        self.assertIn(document2, results)
        self.assertNotIn(document3, results)

    def test_build_document_json(self):
        creator_user = User.objects.create_user('test-user')
        cowriter_user = User.objects.create_user('cowriter-user')
        participant_user = User.objects.create_user('participant-user')
        document = Training.objects.create(resource_id='resource_id_test', title='toto', type='document', creator=creator_user, is_displayed=True, is_deleted=False)
        document.cowriters.add(cowriter_user)
        document.participants.add(participant_user)

        creator = ProfileHelper.get_user_json(creator_user)
        cowriters = [ProfileHelper.get_user_json(cowriter) for cowriter in document.cowriters.all()]
        participants = [{'id' : participant.id} for participant in document.participants.all()]

        json_expected = {'resource' : { 'id' : document.resource_id, 'type' : document.type, 'title' : unicode(document.title), 'updated' : document.last_updated}, 'creator' : creator, 'cowriters' : cowriters, 'participants': participants}

        self.assertEqual(GoogleDriveHelper._build_document_json(document), json_expected)