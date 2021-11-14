import urllib3, datetime
from pathlib import Path
from unittest.mock import patch
from datetime import datetime as dt

from django.test import TestCase
from django.test import LiveServerTestCase, RequestFactory
from urllib3.packages.six import assertCountEqual

from configurateur.models import Station
from donneur.commons import AeroDataStations, CDPDataStations, ManagerData
from donneur.commons import retrieveDatasCDPH_om, retrieveDatasCDPQ_om, retrieveDatasAero
from donneur.commons import retrieveDatasCDPH_metropole, retrieveDatasCDPQ_metropole

# Create your tests here.
class RetrieveData_TestCase(TestCase):
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

    @patch("donneur.commons.request_data_cdp")
    def test_retrieve_datas(self, mock_request_data_cdp):
        """ Test le décryptage des données issues du cdp aéro """
        
        # Test une récupération des données via les SA CDP simulés par le TC1
        mock_request_data_cdp.side_effect=[
            #self.get_data_tc('1','cdph'), 
            #self.get_data_tc('1','cdphom'), 
            #self.get_data_tc('1','cdpq'), 
            #self.get_data_tc('1','cdpqom'), 
            self.get_data_tc('1','cdpaero'), 
        ]
        aeros = retrieveDatasAero([     ('LFPG', '9552761', False), 
                                        ('LFPO', '9405461', False),
                                        ('TFFR', '9710101', True),
                                        ('LFSB', '6829761', False),])
        
        datas = AeroDataStations()
        datas.load_datas(aeros)

        # récupère une ligne d'info
        TFFR = datas.getStation('TFFR')
        self.assertEqual(len(TFFR.echeances), 1)
        heure = TFFR.echeances[dt(2021,11,11,13,0,0)] 
        
        LFPO = datas.getStation('LFPO')
        self.assertEqual(len(LFPO.echeances), 1)

        LFPG = datas.getStation('LFPG')
        self.assertEqual(len(LFPG.echeances), 1)
        
        LFSB = datas.getStation('LFSB')
        self.assertEqual(len(LFSB.echeances), 0)
        
        #.echeances[dt(2021,11,11,13,0,0)].wwTAF)
        
    @patch("donneur.commons.request_data_cdp")
    def test_report_becmg_tempo(self, mock_request_data_cdp):
        """ Test si le report des becmg tempo... sont bien pris en compte """
        
        # Test une récupération des données via les SA CDP simulés par le TC1
        num_TC = '2'
        mock_request_data_cdp.side_effect=[
            #self.get_data_tc(num_TC,'cdph'), 
            #self.get_data_tc(num_TC,'cdphom'), 
            #self.get_data_tc(num_TC,'cdpq'), 
            #self.get_data_tc(num_TC,'cdpqom'), 
            self.get_data_tc(num_TC,'cdpaero'), 
        ]

        stations = self.get_stations()
        aeros = retrieveDatasAero(stations)
        
        datas = AeroDataStations()
        datas.load_datas(aeros)

        # récupère une ligne d'info
        station = datas.getStation('LFRB')
        echeances = [dt(2021,11,12,6,0,0),dt(2021,11,12,7,0,0),dt(2021,11,12,8,0,0),dt(2021,11,12,9,0,0),]
        ww  = [ station.echeances[echeance].get_WW() for echeance in echeances]
        self.assertEqual([['RADZ'],['RADZ'],['RADZ'],['RADZ']], ww) # Test TEMPO N/M => report WW à M inclus

        echeances = [dt(2021,11,12,10,0,0),dt(2021,11,12,11,0,0),dt(2021,11,12,12,0,0)]
        ww  = [ station.echeances[echeance].get_WW() for echeance in echeances]
        self.assertEqual([['SHRA'],['SHRA'],['SHRA'],], ww) # Test PROB40 TEMPO N/M => report WW à M inclus
        
        station = datas.getStation('LFBE')
        echeances = [dt(2021,11,12,20,0,0),dt(2021,11,12,21,0,0),dt(2021,11,12,22,0,0)]
        ww  = [ station.echeances[echeance].get_WW() for echeance in echeances]
        self.assertEqual([['FG'],['FG'],['FG'],], ww) # Test BECMG N/M => WW dès N 
        
        station = datas.getStation('LFBI')
        echeances = [dt(2021,11,12,19,0,0)]
        ww  = [ station.echeances[echeance].get_WW() for echeance in echeances]
        self.assertEqual([['FG','FZFG','RADZ']], ww) # Test Si FZFG => ajoute FG (cf LFBI)

        station = datas.getStation('LFCR')
        echeances = [dt(2021,11,12,20,0,0)]
        ww  = [ station.echeances[echeance].get_WW() for echeance in echeances]
        self.assertEqual([['BR', 'GR','GS']], ww) # Test Si GR => ajoute GS (cf LFCR)

        station = datas.getStation('LFBE')
        echeances = [dt(2021,11,12,11,0,0),dt(2021,11,12,12,0,0)]
        ww  = [ station.echeances[echeance].VVmin for echeance in echeances]
        self.assertEqual([400, 10000], ww) # Test visi BECMG N/M => report phéno précédent jusqu'à M inclus (cf LFBE)

        station = datas.getStation('LFOB')
        echeances = [ dt(2021,11,12,6,0,0),dt(2021,11,12,7,0,0),dt(2021,11,12,8,0,0), dt(2021,11,12,9,0,0)]
        ww  = [ station.echeances[echeance].VVmin for echeance in echeances]
        self.assertEqual([150, 150, 150, 400], ww) # Test visi TEMPO N/M => report de la visi jusqu'à M inclus (cl LFOB)

        station = datas.getStation('LFRD')
        echeances = [ dt(2021,11,12,6,0,0),dt(2021,11,12,7,0,0),dt(2021,11,12,8,0,0), dt(2021,11,12,9,0,0), dt(2021,11,12,10,0,0)]
        ww  = [ station.echeances[echeance].VVmin for echeance in echeances]
        self.assertEqual([1500, 1500, 1500, 1500, 3000], ww) # Test visi PROB40 TEMPO N/M => report de la visi jusqu'à M inclus (cl LFRD)
        
        station = datas.getStation('LFRD')
        echeances = [ dt(2021,11,12,11,0,0),dt(2021,11,12,12,0,0),dt(2021,11,12,13,0,0), dt(2021,11,12,14,0,0), dt(2021,11,12,15,0,0)]
        ww  = [ station.echeances[echeance].FF for echeance in echeances]
        self.assertEqual([15, 15, 15, 15, 12], ww) # Test vent PROB40 TEMPO N/M => report du FF jusqu'à M inclus (cl LFRD)
        ww  = [ station.echeances[echeance].FX for echeance in echeances]
        self.assertEqual([25, 25, 25, 25, 12], ww) # Test vent PROB40 TEMPO N/M => report du FX jusqu'à M inclus (cl LFRD)

        station = datas.getStation('LFTH')
        echeances = [ dt(2021,11,12,6,0,0),dt(2021,11,12,18,0,0),dt(2021,11,12,19,0,0)]
        ww  = [ station.echeances[echeance].FF for echeance in echeances]
        self.assertEqual([15, 15, 10], ww) # Test vent TEMPO N/M => report du FF jusqu'à M inclus (cl LFTH)
        ww  = [ station.echeances[echeance].FX for echeance in echeances]
        self.assertEqual([30, 30, 10], ww) # Test vent TEMPO N/M => report du FX jusqu'à M inclus (cl LFTH)

    @patch("donneur.commons.request_data_cdp")
    def test_retrieve_datas_CDPH(self, mock_request_data_cdp):
        """ Test le décryptage des données issues du cdp h """
        
        # Test une récupération des données via les SA CDP simulés par le TC1
        mock_request_data_cdp.side_effect=[
            self.get_data_tc('3','cdph'), 
            self.get_data_tc('3','cdpq'), 
            self.get_data_tc('3','cdphom'), 
            self.get_data_tc('3','cdpqom'), 
            
            #self.get_data_tc('1','cdpaero'), 
        ]
        stations = self.get_stations()

        cdph = retrieveDatasCDPH_metropole( [(oaci, insee) for oaci, insee, om in stations if not om])
        cdpq = retrieveDatasCDPQ_metropole ([(oaci, insee) for oaci, insee, om in stations if not om])
        cdph_om = retrieveDatasCDPH_om( [(oaci, insee) for oaci, insee, om in stations if om])
        cdpq_om = retrieveDatasCDPQ_om ([(oaci, insee) for oaci, insee, om in stations if om])
        
        datas = CDPDataStations()
        datas.load_datas(cdph, False)
        datas.load_datas(cdph_om, True)
        
        # récupère une ligne d'info
        station = datas.getStation('LFPG')
        heure = station.get_echeance(dt(2021,11,12,10,0,0))
        self.assertEqual(heure.get_param('t'), 2.5000) #2.5000;
        self.assertEqual(heure.get_param('ff'), 10) #9.71920;
        self.assertEqual(heure.get_param('fx'), 10) #0.00000;
        self.assertEqual(heure.get_param('ww'), ['FG']) #1;
        self.assertEqual(heure.get_param('rr1'), 0) #0.0000;
        self.assertEqual(heure.get_param('rr3'), 0) #0.0000;
        self.assertEqual(heure.get_param('rr6'), 0) #0.0000;
        self.assertEqual(heure.get_param('rr12'), 0) #0.0000;
        self.assertEqual(heure.get_param('rr24'), 1) #1.0000;
        self.assertEqual(heure.get_param('etatsol'), 0) #0;
        self.assertEqual(heure.get_param('pneige'), 0) #0.0000;
        self.assertEqual(heure.get_param('dd'), 160) #160;

        station = datas.getStation('TFFR')
        heure = station.get_echeance(dt(2021,11,12,12,0,0))
        #9710101;2021-11-12 12:00:00;2021-11-12 17:48:01;27.3000;3.88768;0.00000;18;-999;2.0000;55;
        self.assertEqual(heure.get_param('t'), 27.3) #27.3000;
        self.assertEqual(heure.get_param('ff'), 4) #3.88768;
        self.assertEqual(heure.get_param('fx'), 4) #0.00000;
        self.assertEqual(heure.get_param('ww'), ['RA']) #18;
        self.assertEqual(heure.get_param('etatsol'), -999) #-999;
        self.assertEqual(heure.get_param('rr1'), 0.33) #2.0000;
        self.assertEqual(heure.get_param('rr3'), 1.0) #2.0000;
        self.assertEqual(heure.get_param('rr6'), 2) #2.0000;
        self.assertEqual(heure.get_param('rr12'), 4) #2.0000;
        self.assertEqual(heure.get_param('dd'), 55) #55;
        """"'t','t/10'),('ff','ff*1.94384'),('fx','fx*1.94384'),('ww','w1'),('etatsol','etatsol'),
                        ('rr6','rrcum_omfutur(adddate(dvalid,INTERVAL 6 HOUR),ID,0)/10'),('dd','dd')]"""

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

    @patch("donneur.commons.request_data_cdp")
    def test_assembleur(self, mock_request_data_cdp):
        """ Test la classe qui assemble les données issus des cdp """
        
        # Récupération des données via les SA CDP simulés par le TC1
        num_TC = '4'
        mock_request_data_cdp.side_effect=[
            self.get_data_tc(num_TC,'cdpaero'),
            self.get_data_tc(num_TC,'cdph'), 
            self.get_data_tc(num_TC,'cdpq'), 
            #self.get_data_tc(num_TC,'cdphom'), 
            #self.get_data_tc(num_TC,'cdpqom'),  
        ]
        
        stations = [('LFRN', '3528161', False)]
        
        aeros = retrieveDatasAero(stations)
        datas_aero = AeroDataStations()
        datas_aero.load_datas(aeros)

        cdph = retrieveDatasCDPH_metropole( [(oaci, insee) for oaci, insee, om in stations if not om])
        cdpq = retrieveDatasCDPQ_metropole ([(oaci, insee) for oaci, insee, om in stations if not om])
        datas = CDPDataStations()
        datas.load_datas(cdph, False)
        #datas.load_datas(cdpq, False) # Ajout des données quotidiennes pas encore implémenté
        
        # Chargement dans l'assembleur. C'est lui qui va répondre au tests. 
        assembleur = ManagerData(datas_aero, datas)
        
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,0,0,0), 'LFRN'), [])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,1,0,0), 'LFRN'), ['TS', 'VENT'])
        self.assertEqual( assembleur.question_declenche('LFRN', dt(2021,11,11,1,0,0), 'TS', ''), True)

        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,2,0,0), 'LFRN'), ['GR'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,3,0,0), 'LFRN'), ['FG', 'FZDZ', 'FZRA', 'SQ'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,4,0,0), 'LFRN'), ['FG','FZFG', 'VENT'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,5,0,0), 'LFRN'), ['DENSE_FG', 'FG'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,6,0,0), 'LFRN'), ['TMIN'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,7,0,0), 'LFRN'), ['TMAX'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,8,0,0), 'LFRN'), ['RR24'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,9,0,0), 'LFRN'), ['RR1', 'RR12', 'RR24', 'RR3', 'RR6'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,10,0,0), 'LFRN'), [])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,11,0,0), 'LFRN'), ['TS', 'VENT'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,12,0,0), 'LFRN'), ['GR'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,13,0,0), 'LFRN'), ['FG', 'FZFG'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,14,0,0), 'LFRN'), ['FZRA'])
        self.assertEqual( self.batterie_tests(assembleur, dt(2021,11,11,15,0,0), 'LFRN'), ['FG'])

