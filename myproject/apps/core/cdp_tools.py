from pathlib import Path
import datetime, json
import sys, urllib3

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from myproject.apps.core.models import Region, Station, Profile, ConfigMAA, EnvoiMAA, Client, MediumMail, Log
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

class DataStation(object):
    def __init__(self, oaci):
        self.oaci = oaci
        self.echeances = {}
    
    def add_echeance(self, dt, data):
        """"
            Insère une ligne de données: 
            dt : datetime représentant l'échéance de la donnée
            data : objet DataEcheance
        """
        self.echeances[dt] = data

    def get_echeance(self, dt):
        return self.echeances(dt)
    
    def get_echeances(self):
        ''' Retourne un tableau des data avec les echeances triées chronologiquement'''
        ech = sorted(self.echeances.keys())
        return [ self.echeances[key] for key in ech]

class DataEcheance(object):
    PARAMETRES = [
            'id','dprod','dvalid','idoaci','DateEmissionTAF','visi','visiprob40','VisibiliteTempo','VisibiliteProb40Tempo',
            'ddtaf','DDTAFTempo','DDTAFProb40','DDTAFProb40Tempo',
            'FFTAF','FFTAFTempo','FFTAFProb40','FFTAFProb40Tempo','FXTAF','FXTAFTempo','FXTAFProb40','FXTAFProb40Tempo',
            'wwTAF','wwTAFTempo','wwTAFProb40','wwTAFProb40Tempo'
        ]
    def __init__(self, ligne, mustTranspose, dateRef):
        """ Décompose une ligne de données CDP Aéro en données DataEchenace
            mustTranspose : si None, pas d'action sur les dates. Si datetime, indique la cible de la translation
            dateRef : utilisé que si mustTranspose n'est pas None. dateRef est alors la date de référence du fichier CDP aero qu'il faut translater
        """
        super().__init__()
        infos = ligne.split(';')
        for index, val in enumerate(infos[:-1]):
            self.__dict__[self.PARAMETRES[index]] = val.strip()
        
        if mustTranspose:
            delta = mustTranspose - dateRef

        dates = ['dprod', 'dvalid']
        for date in dates:
            dt = self.__dict__.get(date, None)
            if dt:
                self.__dict__[date] = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                if mustTranspose:
                    self.__dict__[date] = self.__dict__[date] + delta

class CDPAero(object):
    def __init__(self):
        self.remote_url = settings.REMOTE_CDPAERO
        self.profondeur = "-3,48"
        self.format = 'csv'
        self.parametres = DataEcheance.PARAMETRES
        self.repertoire_TC = settings.BASE_DIR.joinpath('myproject').joinpath('apps').joinpath('core').joinpath('tests')
        self.data_stations = {}

    def define_url(self):
        """ Définit l'url de la requête """
        parametres = {}
        parametres['dpivot'] = self.profondeur
        parametres['format'] = self.format
        parametres['param'] = ','.join(self.parametres)
        parametres['id'] = self.get_liste_insee()
        return self.remote_url + "&".join([param + "=" + value for param, value in parametres.items()])

    def get_liste_insee(self):
        """ Récupère la liste des codes inseepp à partie des stations configurées """
        stations = Station.objects.all()
        insee = []
        for station in stations:
            insee.append(station.inseepp)
        return ",".join(insee)

    def get_remote_data_cdpaero(self):
        url = self.define_url()
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

    def get_TC_data_cdpaero(self, TC, transpose_date=None):
        """ Récupère les données de toutes les stations sur le cdp aero stocké en local (données TAF des TC) 
            TC doit prendre la valeur d'un répertoire de test dans lequel ont trouve un fichier cdpaero.csv
            Si transpose_date n'est pas None, elle représente un datetime. Les dates sont alors translatées par rapport à la date transpose_date 
            et la date de la première ligne.
        """
        repertoire = self.repertoire_TC.joinpath(TC)
        fichier = repertoire.joinpath("cdpaero.csv")

        self.transpose_date = transpose_date

        if not fichier.exists():
            raise FileExistsError("Le fichier {} n'existe pas".format(fichier) )
        
        with open(fichier, 'r') as ficin:
            transpose = ficin.readline()
            self.transpose = datetime.datetime.strptime(transpose.strip(), "%Y-%m-%d %H:%M:%S")
            nb_ligne = ficin.readline()
            for ligne in ficin.readlines():
                ligne = ligne.strip()
                if ligne:
                    self.add_data_line(ligne)

        return self.data_stations

    def add_data_line(self, ligne):
        """ Prend une ligne de cdp aero est la disseque pour récupérer les infos """
        data = DataEcheance(ligne, self.transpose_date, self.transpose)
        
        dvalid = data.dvalid
        if dvalid.minute ==0:
            data_station = self.data_stations.get(data.idoaci, DataStation(data.idoaci))
            data_station.add_echeance(data.dvalid, data)
            self.data_stations[data.idoaci] = data_station

    def get_data_station(self, oaci): 
        """ Retourne les données d'une station définie par oaci"""
        return self.data_stations.get(oaci, None)

    def get_data_cdpaero(self, TC=None, transpose_date=None):
        """ Récupère les données de toutes les stations sur le cdp aero (données TAF) 
            Si TC = None, on cherche à récupérer les données sur le SA CDP Aéro
            Sinon, doit prendre la valeur d'un répertoire de test dans lequel ont trouve un fichier cdpaero.csv
            Si transpose_date n'est pas None, elle représente un datetime. Les dates sont alors translatées par rapport à la date transpose_date 
            et la date de la première ligne.
        """
        if TC is None:
            return self.get_remote_data_cdpaero()
        else:
            return self.get_TC_data_cdpaero(TC, transpose_date)
        