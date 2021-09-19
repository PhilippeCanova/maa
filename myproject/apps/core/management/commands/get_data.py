from pathlib import Path
import datetime, json
import sys, urllib3

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from myproject.apps.core.models import Region, Station, Profile, ConfigMAA, EnvoiMAA, Client, MediumMail, Log
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings



class Command(BaseCommand):
    help = 'Lance les requêtes pour récupérer les data en ws sur cdp aero et cdp h et q'

    def add_arguments(self, parser):
        #parser.add_argument('--onlydelete', action="store_true", help="Permet de demander l'effacement des champs déjà en base (hors superuser)")
        #parser.add_argument('--create', action="store_true", help="Permet de demander la création des champs en base (hors superuser)")
        pass

    def get_data_cdpaero(self):
        """ Récupère les données de toutes les stations sur le cdp aero (données TAF) """
        stations = Station.objects.all()
        insee = []
        for station in stations:
            insee.append(station.inseepp)
        liste_insee = ",".join(insee)

        parametres = {}
        url = settings.REMOTE_CDPAERO

        parametres['dpivot'] = "-3,48"
        parametres['format'] = "csv"
        parametres['param'] = 'id,dprod,dvalid,dinsert,idoaci,DateEmissionTAF,'
        parametres['param'] = parametres['param']  + 'visi,visiprob40,VisibiliteTempo,VisibiliteProb40Tempo,'
        parametres['param'] = parametres['param']  + 'ddtaf,DDTAFTempo,DDTAFProb40,DDTAFProb40Tempo,'
        parametres['param'] = parametres['param']  + 'FFTAF,FFTAFTempo,FFTAFProb40,FFTAFProb40Tempo,FXTAF,FXTAFTempo,FXTAFProb40,FXTAFProb40Tempo,'
        parametres['param'] = parametres['param']  + 'wwTAF,wwTAFTempo,wwTAFProb40,wwTAFProb40Tempo'
        parametres['id'] = liste_insee
        

        url = url + "&".join([param + "=" + value for param, value in parametres.items()])
        print(url)

        http = urllib3.PoolManager()
        try: 
            r = http.request('GET', url, timeout=10.0)
            if r.status != '200':
                print ("Erreur")
            else:
                data = json.loads(r.data.decode('utf-8'))
                print (r.data)
                print (data)

        except urllib3.exceptions.RequestError as E:
            print (E)


        return None

    def handle(self, *args, **options):
        cdpaero = self.get_data_cdpaero()