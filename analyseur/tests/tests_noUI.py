import urllib3, datetime
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta

from django.test import TestCase
from django.db import models
from django.test import LiveServerTestCase, RequestFactory
from urllib3.packages.six import assertCountEqual

from configurateur.models import Station, ConfigMAA
from donneur.commons import AeroDataStations, CDPDataStations, ManagerData
from donneur.commons import retrieveDatasCDPH_om, retrieveDatasCDPQ_om, retrieveDatasAero
from donneur.commons import retrieveDatasCDPH_metropole, retrieveDatasCDPQ_metropole
from analyseur.commons import define_open_airport
from analyseur.models import EnvoiMAA

# Create your tests here.
class AnalyseData_TestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Utlisé pour une utilisation commune à toutes les fonctions test de cette clasee 
            mais lancé une seule fois """

        # Insertion en base des données initiales. Permet d'avoir une liste des stations aéro
        from myproject.apps.core.management.commands.initiate import Initiate
        super().setUpClass()
        init = Initiate()
        init.delete()
        init.create()

    def setUp(self):
        """ Executée à chaque lancement d'une fonction test_ de cette classe 
            TODO: enelever ensuite si pas utilisée.
        """
        pass

    def tearDown(self):
        """ Executée après chaque lancement d'une fonction test_ de cette classe 
            TODO: enelever ensuite si pas utilisée.
        """
        pass

    def get_data_tc(self, num_TC, fichier): 
        """ Récupère les données aéro et cdp du cas de TC cité """
        repertoire = Path(__file__).parent.joinpath('TC'+num_TC)
        if not repertoire.exists():
            raise FileExistsError("Le répertoire {} n'existe pas".format(repertoire) )

        fichier = repertoire.joinpath(fichier + '.csv')
        if not fichier.exists():
            raise FileExistsError("Le ficheir {} n'existe pas".format(fichier) )
        
        with open(fichier, 'r') as ficin:
            return ficin.read()
        
        raise KeyError("Imposible de trouver le fichier {} du TC{}".format(fichier, numTC))

    def get_stations(self):
        """ Permet de générer un tableau avec les infos des stations nécessaire au lancement des extractions """
        stations_objects = Station.objects.all()
        stations = []
        for station in stations_objects:
            stations.append(( station.oaci, station.inseepp, station.outremer ))
        return stations

    def batterie_tests(self, manager, echeance, oaci):
        """ Permet de tester tous les types de MAA sur l'écheance et la station données.

            Pour les cumuls, les seuils sont pris à 50mm
            Pour les vents, le seuil est de 50 kt
            Pour les températures, les seuils sont <-1 et >30 
        
            Retourne une liste ordonnée des types ayant déclenchés
        """
        positif = []
        conforme = True
        if manager.question_declenche(oaci, echeance, 'VENT', 50): positif.append('VENT')
        if manager.question_declenche(oaci, echeance, 'TMIN', -1): positif.append('TMIN')
        if manager.question_declenche(oaci, echeance, 'TMAX', 30): positif.append('TMAX')
        if manager.question_declenche(oaci, echeance, 'RR1', 50): positif.append('RR1')
        if manager.question_declenche(oaci, echeance, 'RR3', 50): positif.append('RR3')
        if manager.question_declenche(oaci, echeance, 'RR6', 50): positif.append('RR6')
        if manager.question_declenche(oaci, echeance, 'RR12', 50): positif.append('RR12')
        if manager.question_declenche(oaci, echeance, 'RR24', 50): positif.append('RR24')
        if manager.question_declenche(oaci, echeance, 'TS') : positif.append('TS')
        if manager.question_declenche(oaci, echeance, 'GR'): positif.append('GR')
        if manager.question_declenche(oaci, echeance, 'SQ'): positif.append('SQ')
        if manager.question_declenche(oaci, echeance, 'FG'): positif.append('FG')
        if manager.question_declenche(oaci, echeance, 'FZRA'): positif.append('FZRA')
        if manager.question_declenche(oaci, echeance, 'FZFG'): positif.append('FZFG')
        if manager.question_declenche(oaci, echeance, 'FZDZ'): positif.append('FZDZ')
        if manager.question_declenche(oaci, echeance, 'DENSE_FG'): positif.append('DENSE_FG')

        return sorted(positif)

    def test_heure_ouverture_station(self):
        """ Test la bonne prise en charge des heures d'ouverture et fermeture.
            D'autres tests plus spécifiques sont faits dans ConfigurateurTestCase pour la prise en charge du changement d'heure
        """
        # Test sur LFRQ fermée de 22TU à 05TU (selon config tempo des stations)
        NOW = datetime(2021,11,12,12,0,0) # Milieu de journée, LFRQ est ouverte
        stations = define_open_airport(NOW)
        self.assertEqual(type(stations.get(oaci="LFRQ")), Station)

        NOW = datetime(2021,11,12,0,0,0) # En pleine période de fermeture, LFRQ est fermée
        stations = define_open_airport(NOW)
        self.assertRaises(Station.DoesNotExist, stations.get, oaci="LFRQ")
        
        NOW = datetime(2021,11,12,22,0,0) # A l'heure pile de fermeture, LFRQ est ouverte
        stations = define_open_airport(NOW)
        self.assertEqual(type(stations.get(oaci="LFRQ")), Station)

        NOW = datetime(2021,11,12,22,1,0) # LFRQ encore ouverte
        stations = define_open_airport(NOW)
        self.assertRaises(Station.DoesNotExist, stations.get, oaci="LFRQ")

        NOW = datetime(2021,11,12,4,59,0) # Une minute avant l'ouverture, LFRQ est encore fermée
        stations = define_open_airport(NOW)
        self.assertRaises(Station.DoesNotExist, stations.get, oaci="LFRQ")

        NOW = datetime(2021,11,12,5,0,0) # A l'heure pile de l'ouverture, LFRQ est enfin ouverte
        stations = define_open_airport(NOW)
        self.assertEqual(type(stations.get(oaci="LFRQ")), Station)

        # Pour LFPG, ouverture 00:00 et fermeture à 23:59
        NOW = datetime(2021,11,12,0,0,0) # LFPG est ouverte
        stations = define_open_airport(NOW)
        self.assertEqual(type(stations.get(oaci="LFPG")), Station)

        NOW = datetime(2021,11,12,23,59,0) # LFPG est ouverte
        stations = define_open_airport(NOW)
        self.assertEqual(type(stations.get(oaci="LFPG")), Station)

        NOW = datetime(2021,11,12,23,59,54) # LFPG est ouverte
        stations = define_open_airport(NOW)
        self.assertEqual(type(stations.get(oaci="LFPG")), Station)

    def test_maa_en_cours(self):
        """ Teste la bonne gestion des récupérations des MAA en cours
        """
        station = Station.objects.get(oaci='LFPG')

        NOW = datetime.utcnow()

        # Récupère l'envoi configuré dans la base pour LFPG, pour un MAA de TS
        envoi = EnvoiMAA.objects.get(configmaa__station__oaci = 'LFPG')
        envoi.date_fin = NOW - timedelta(days=5) # Fait en sorte que le maa soit terminé
        envoi.date_envoi = NOW - timedelta(days=5)
        envoi.save()

        # Test le filter des envois historiques:
        maas = EnvoiMAA.objects.history_maas() # Supposé retourner tous les MAA de moins de 48h
        self.assertEqual(len(maas), 0)

        envoi.date_fin = NOW - timedelta(days=1)
        envoi.date_envoi = NOW - timedelta(days=1)
        envoi.save()
        maas = EnvoiMAA.objects.history_maas() # Supposé retourner tous les MAA de moins de 48h
        self.assertEqual(len(maas), 1) # On trouve celui de LFPG

        self.assertEqual(len(EnvoiMAA.objects.current_maas()), 0)
        self.assertEqual(len(EnvoiMAA.objects.current_maas_by_station('LFPG')), 0)
        self.assertIsInstance(EnvoiMAA.objects.current_maas_by_type('LFPG', 'TS'), type(None))

        # Test le repérage d'un MAA en cours de validité
        envoi.date_fin = NOW + timedelta(hours=3)
        envoi.date_envoi = NOW - timedelta(hours=1)
        envoi.save()
        self.assertEqual(len(EnvoiMAA.objects.history_maas()), 1) # On trouve celui de LFPG
        self.assertEqual(len(EnvoiMAA.objects.current_maas()), 1)
        self.assertEqual(len(EnvoiMAA.objects.current_maas_by_station('LFPG')), 1)
        self.assertEqual(len(EnvoiMAA.objects.current_maas_by_station('LFRN')), 0)
        self.assertIsInstance(EnvoiMAA.objects.current_maas_by_type('LFPG', 'TS'), EnvoiMAA)
        self.assertIsInstance(EnvoiMAA.objects.current_maas_by_type('LFPG', 'VENT'), type(None))

        
        # Test la récupération d'un maa de type seuil
        config = ConfigMAA.objects.get(station__oaci = 'LFPG', type_maa = 'VENT', seuil=25.0)
        envoi = EnvoiMAA.objects.create( 
            configmaa = config,
            date_envoi = NOW - timedelta (hours= 3),
            date_debut = NOW.replace(minute =0).replace(second=0) + timedelta (hours= 3),
            date_fin = NOW.replace(minute =0).replace(second=0) + timedelta (hours= 8),
            numero = 1,
            fcst=True,
            status = 'to_send',
            message = """LFBT AD WRNG 1 VALID 201356/201500""",
            context_TAF = """0,35,""",
            log = "Ici, les logs de création",
            message_mail = 'Corps du mail',
            message_sms = "message SMS",
        )
        envoi.save()

        self.assertEqual(len(EnvoiMAA.objects.history_maas()), 2) # On trouve celui de LFPG
        self.assertEqual(len(EnvoiMAA.objects.current_maas()), 2)
        self.assertEqual(len(EnvoiMAA.objects.current_maas_by_station('LFPG')), 2)
        self.assertEqual(len(EnvoiMAA.objects.current_maas_by_station('LFRN')), 0)
        self.assertIsInstance(EnvoiMAA.objects.current_maas_by_type('LFPG', 'TS'), EnvoiMAA)
        self.assertIsInstance(EnvoiMAA.objects.current_maas_by_type('LFPG', 'VENT', NOW, 30), type(None))
        self.assertIsInstance(EnvoiMAA.objects.current_maas_by_type('LFPG', 'VENT', NOW, 25), EnvoiMAA)

    def test_maa_delai_retention(self):
        """ Teste la bonne gestion du dépassement du délai de rétention
        """
        from analyseur.commons import delai_retention_depasse
        from analyseur.commons import bientot_fini
        
        station = Station.objects.get(oaci='LFPG')
        station.retention = 3

        NOW = datetime(2021,11,12,0,0,0)

        # Récupère l'envoi configuré dans la base pour LFPG, pour un MAA de TS
        envoi = EnvoiMAA.objects.get(configmaa__station__oaci = 'LFPG')
        #envoi.date_fin = NOW - timedelta(days=5) # Fait en sorte que le maa soit terminé
        envoi.date_fin = NOW + timedelta(minutes=150)
        envoi.date_envoi = NOW - timedelta(hours=2)
        envoi.save()

        # Avec cette config, on n'a pas passé la limite de rétention et il n'est pas bientôt fini
        self.assertEqual(delai_retention_depasse(NOW, envoi), False)
        self.assertEqual(bientot_fini(NOW, envoi), False)


        # Avec cette config, on a pas passé la limite de rétention et il est bientôt fini
        NOW = datetime(2021,11,12,2,0,0)
        self.assertEqual(delai_retention_depasse(NOW, envoi), True)
        self.assertEqual(bientot_fini(NOW, envoi), True)
        

    def test_debut_plage_recherche(self):
        """ Teste la fonction de définition de la place horaire potentiel d'un début de MAA
        """
        from analyseur.commons import define_start_laptime

        station = Station.objects.get(oaci='LFPG')
        configmaa = ConfigMAA.objects.filter(station=station).filter(type_maa = 'TS')
        configmaa.scan = 3

        NOW = datetime(2021,11,12,8,0,0)

        periode = define_start_laptime(NOW, configmaa)
        match = [ datetime(2021,11,12,8,0,0), datetime(2021,11,12,9,0,0), datetime(2021,11,12,10,0,0), datetime(2021,11,12,11,0,0), ]
        self.assertListEqual(periode, match)
    
    def get_assembleur_data(self, stationsQuery):
        # Récupération des données via les SA CDP simulés par le TC1
        

        stations = []
        for station in stationsQuery:
            stations.append( (station.oaci, station.inseepp, station.outremer))

        aeros = retrieveDatasAero(stations)
        datas_aero = AeroDataStations()
        datas_aero.load_datas(aeros)

        cdph = retrieveDatasCDPH_metropole( [(oaci, insee) for oaci, insee, om in stations if not om])
        cdpq = retrieveDatasCDPQ_metropole ([(oaci, insee) for oaci, insee, om in stations if not om])
        cdph_om = retrieveDatasCDPH_metropole( [(oaci, insee) for oaci, insee, om in stations if om])
        cdpq_om = retrieveDatasCDPQ_metropole ([(oaci, insee) for oaci, insee, om in stations if om])
        datas = CDPDataStations()
        datas.load_datas(cdph, False)
        #datas.load_datas(cdpq, False) # Ajout des données quotidiennes pas encore implémenté
        
        # Chargement dans l'assembleur. C'est lui qui va répondre au tests. 
        return ManagerData(datas_aero, datas)

    @patch("donneur.commons.request_data_cdp")
    def test_declenche_debut(self, mock_request_data_cdp):
        """ Teste la récupération du début d'un maa éventuel
        """
        from analyseur.commons import recherche_debut_maa, define_start_laptime

        num_TC = '1'
        mock_request_data_cdp.side_effect=[
            self.get_data_tc(num_TC,'cdpaero'),
            self.get_data_tc(num_TC,'cdph'), 
            self.get_data_tc(num_TC,'cdpq'), 
            self.get_data_tc(num_TC,'cdphom'), 
            self.get_data_tc(num_TC,'cdpqom'),  
        ]

        assembleur = self.get_assembleur_data(Station.objects.all())

        configmaa = ConfigMAA.objects.get(station__oaci='LFRN', type_maa = 'TS')
        configmaa.scan = 3 # Fixe le scan pour comparaison
        configmaa.seuil= None # S'assure de la valeur du seuil

        NOW = datetime(2021,11,11,0,0,0)

        periode = define_start_laptime(NOW, configmaa)

        debut = recherche_debut_maa(assembleur, 'LFRN', periode, configmaa)
        self.assertEqual(debut, datetime(2021,11,11,1))

    @patch("donneur.commons.request_data_cdp")
    def test_analyse_15mn(self, mock_request_data_cdp):
        """ Test la bonne prise en charge des heures d'ouverture et fermeture.
            D'autres tests plus spécifiques sont faits dans ConfigurateurTestCase pour la prise en charge du changement d'heure
        """
        from analyseur.commons import analyse_15mn

        num_TC = '2'
        mock_request_data_cdp.side_effect=[
            self.get_data_tc(num_TC,'cdpaero'),
            self.get_data_tc(num_TC,'cdph'), 
            self.get_data_tc(num_TC,'cdpq'), 
            self.get_data_tc(num_TC,'cdphom'), 
            self.get_data_tc(num_TC,'cdpqom'),  
        ]

        NOW = datetime(2021,11,11,0,0,0)
        analyse_15mn(NOW)



