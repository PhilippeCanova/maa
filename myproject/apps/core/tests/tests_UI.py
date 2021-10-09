from django.test import TestCase
from django.test import LiveServerTestCase
import pdb;

from selenium import webdriver # Pour utiliser Selenium
from myproject.apps.core.models import Region, Station, Profile, ConfigMAA, EnvoiMAA, Client, MediumMail, Log
from django.contrib.auth.models import User, Group, Permission

from myproject.apps.core.management.commands.initiate import Initiate
# Create your tests here.
class ConnexionTestCase(LiveServerTestCase):
    def setUp(self):
        """ executé avant chacune des fonction test_
            Pour quelque chose reproduit dans chaque test, prendre plutôt la classe setupClass
        """
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(2)
        #print ("UI tests")

    def tearDown(self):
        """ Executé après chaque fonction test_"""
        self.browser.quit()
        pass

    @classmethod
    def setUpClass(cls):
        """ Utlisé pour une utilisation commune à toutes les fonctions test de cette clasee 
            mais lancé une seule fois """
        super().setUpClass()
        #print('setUpClass')
        init = Initiate()
        init.create()

    @classmethod
    def tearDownClass(cls):
        """ Idem de setUpClass """
        super().tearDownClass()

    def test_connect_to_admin(self):
        home_page = self.browser.get(self.live_server_url + '/admin/')

        # Recherche un élément particulier dans la page
        brand_element = self.browser.find_element_by_css_selector('#site-name')
        self.assertEqual('Administration des MAA', brand_element.text)

        #Pour accéder au formulaire, utiliser le find id
        #login_form = self.browser.find_element_by_id('login-form')
        #Mais ensuite, pour les champs du formulaire qui seront envoyés en POST, prendre le find name
        #login_form.find_element_by_name('username').send_keys('bill')
        user_input = self.browser.find_element_by_css_selector('input#id_username')
        pwd_input = self.browser.find_element_by_css_selector('input#id_password')
        self.assertEqual(user_input.get_attribute('name'), 'username')

        user_input.send_keys('administrateur')
        pwd_input.send_keys('djangofr')
        self.browser.find_element_by_css_selector('.submit-row input').click()

        
        print(self.browser.current_url)
        print (self.live_server_url)

        stations_link = self.browser.find_element_by_link_text('Stations')
    
        self.assertEqual(stations_link.get_attribute('href'),
           self.live_server_url + '/admin/core/station/'
        )
        stations_link.click()

        station_rows = self.browser.find_elements_by_css_selector('#result_list tr')
        headers = station_rows[0].find_elements_by_css_selector('.text')
        self.assertEqual(headers[0].text, 'CODE OACI')

        # Si une nouvelle fenêtre s'ouvre pour la saisie, Selenium peut y accéder avec :
        #self.browser.switch_to.window(self.browser.window_handles[1])