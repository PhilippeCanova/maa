from django.test import TestCase
from django.test import LiveServerTestCase, RequestFactory
from django.urls import resolve
from django.contrib.auth.models import AnonymousUser, User

from selenium import webdriver # Pour utiliser Selenium

from myproject.apps.site.views import WebVFRView

# Create your tests here.
class ConnexionTestCase(LiveServerTestCase):
    def setUp(self):
        """ executé avant toute fonction test_"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='jacob', email='jacob@free.fr', password='top_secret')

    def tearDown(self):
        """ Executé après chaque fonction test_"""
        #self.browser.quit()

    def test_connect_to_admin(self):
        print ("No UI")
        root = resolve('/')
        self.assertEqual(root.func, WebVFRView, "L'url racine arrive n'aboutit pas sur la bonne vue")
        
        request = self.factory.get('/')
        request.user = AnonymousUser() # Simule un anonymous
        response = WebVFRView(request)
        self.assertEqual(response.status_code, 302, "L'url racine / devrait rediriger les non identifiés donc status 302")

        request.user = self.user
        #with self.assertTemplateUsed('site/inde.html', "Le template utilisé n'est pas le bon"):
        response = WebVFRView(request)
        self.assertEqual(response.status_code, 200, "L'url racine / devrait accepter les requêtes de personnes identifiées.")