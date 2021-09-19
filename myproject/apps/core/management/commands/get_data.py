from pathlib import Path
import datetime, json
import sys, urllib3

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from myproject.apps.core.models import Region, Station, Profile, ConfigMAA, EnvoiMAA, Client, MediumMail, Log
from myproject.apps.core.cdp_tools import CDPAero

class Command(BaseCommand):
    help = 'Lance les requêtes pour récupérer les data en ws sur cdp aero et cdp h et q'

    def add_arguments(self, parser):
        
        parser.add_argument('--TC', help="Permet de définir le répertoire dans lequel se trouve le Test Case")
        parser.add_argument('--transpose-date', help="Permet de définir si les dates doivent être transposées")
    

    def handle(self, *args, **options):
        print (options)
        if options['transpose_date'] is not None:
            options['transpose_date'] = datetime.datetime.strptime(options['transpose_date'], "%Y-%m-%d %H:%M:%S")

        cdpaero = CDPAero()
        print (cdpaero.define_url())
        data_aero = cdpaero.get_data_cdpaero(options['TC'], options['transpose_date'])
        
        
        LFPG = data_aero.get('LFPG')
        for ech in LFPG.get_echeances():
            print (ech.id, ech.dvalid, ech.idoaci, ech.DateEmissionTAF, ech.ddtaf, ech.DDTAFTempo, ech.DDTAFProb40, ech.DDTAFProb40Tempo)