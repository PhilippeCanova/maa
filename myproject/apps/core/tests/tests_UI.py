from django.test import TestCase
from django.test import LiveServerTestCase

from selenium import webdriver # Pour utiliser Selenium

# Create your tests here.
class ConnexionTestCase(LiveServerTestCase):
    def setUp(self):
        """ executé avant toute fonction test_"""
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(2)
        print ("UI tests")

    def tearDown(self):
        """ Executé après chaque fonction test_"""
        self.browser.quit()

    def test_connect_to_admin(self):
        home_page = self.browser.get(self.live_server_url + '/admin/')

        # Recherche un élément particulier dans la page
        brand_element = self.browser.find_element_by_css_selector('#site-name')
        self.assertEqual('Administration des MAA', brand_element.text)

        user_input = self.browser.find_element_by_css_selector('input#id_username')
        pwd_input = self.browser.find_element_by_css_selector('input#id_password')
        self.assertEqual(user_input.get_attribute('name'), 'username')

        user_input.send_keys('philippe')
        pwd_input.send_keys('fr')
        user_input.submit()
        # ou self.browser.find_element_by_css_selector('form button').click()
