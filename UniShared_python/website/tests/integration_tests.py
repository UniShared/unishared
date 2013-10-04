'''
Created on Dec 5, 2012

@author: arnaud
'''
"""
from UniShared_python.website.models import UserProfile
from django.contrib.auth.models import User
from django.test.testcases import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from social_auth.db.django_models import UserSocialAuth

class IntegrationLoginTest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.selenium = webdriver.Chrome('/Users/arnaud/Downloads/chromedriver')
        super(IntegrationLoginTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        UserProfile.objects.all().delete()
        UserSocialAuth.objects.all().delete()
        User.objects.all().delete()
        
        cls.selenium.quit()
        super(IntegrationLoginTest, cls).tearDownClass()

    def test_login_student(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/'))

        self.selenium.find_element_by_css_selector("a.fb_connect").click()
        self.selenium.find_element_by_id("email").clear()
        self.selenium.find_element_by_id("email").send_keys("arnaud@unishared.com")
        self.selenium.find_element_by_id("pass").clear()
        self.selenium.find_element_by_id("pass").send_keys("makesense")
        self.selenium.find_element_by_id("loginbutton").click()
        self.selenium.find_element_by_link_text("Student").click()
        
        school_field = self.selenium.find_element_by_id("school")
        
        WebDriverWait(self.selenium, 10).until(
            lambda driver : school_field.is_displayed()
        )
        
        school_field.send_keys("test")
        
        self.selenium.find_element_by_xpath("(//button[@type='submit'])[1]").click()
        
        email_field = self.selenium.find_element_by_id("email")
        
        WebDriverWait(self.selenium, 10).until(
            lambda driver : email_field.is_displayed()
        )
        email_field.send_keys("arnaud@unishared.com")
        self.selenium.find_element_by_xpath("(//button[@type='submit'])[2]").click()
        
        WebDriverWait(self.selenium, 10).until(
            lambda driver : "profile" in self.selenium.current_url 
        )
        
        self.assertTrue("profile" in self.selenium.current_url, 'Not on profile : {0}'.format(self.selenium.current_url))
"""