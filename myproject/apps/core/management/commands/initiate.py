from pathlib import Path
import datetime

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from myproject.apps.core.models import Region, Station, Profile, ConfigMAA, EnvoiMAA, Client, MediumMail
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

class ConfigStation(object):
        def __init__(self, entetes, ligne) -> None:
            super().__init__()
            infos = ligne.split('\t')
            for index, val in enumerate(infos):
                self.__dict__[entetes[index].strip()] = val.strip()


class ConfigsStation(object):
        def __init__(self, fichier) -> None:
            """ Charge les config du fichier"""
            super().__init__()
            self.stations = {}
            with open(fichier, 'r') as ficin:
                entetes = ficin.readline()
                entetes = entetes.split('\t')

                for ligne in ficin.readlines():
                    config = ConfigStation(entetes, ligne)
                    config.date_pivot = datetime.datetime.strptime(config.date_pivot, "%Y-%m-%d %H:%M:%S")
                    config.ouverture = datetime.datetime.strptime(config.ouverture, "%H:%M")
                    config.ouverture1 = datetime.datetime.strptime(config.ouverture1, "%H:%M")
                    config.ouverture2 = datetime.datetime.strptime(config.ouverture2, "%H:%M")
                    if config.fermeture == '24:00': config.fermeture = '23:59'
                    if config.fermeture1 == '24:00': config.fermeture1 = '23:59'
                    if config.fermeture2 == '24:00': config.fermeture2 = '23:59'
                    config.fermeture = datetime.datetime.strptime(config.fermeture, "%H:%M")
                    config.fermeture1 = datetime.datetime.strptime(config.fermeture1, "%H:%M")
                    config.fermeture2 = datetime.datetime.strptime(config.fermeture2, "%H:%M")
                    self.stations[config.station] = config

        def get_station(self, tag):
            return self.stations.get(tag, None)

        def get_dirs(self):
            """ Récupérer un set avec toutes les dirs apparaissant dans les configs"""
            regions = []
            for config in self.stations.values():
                regions.append(config.dir)
            return set(regions)
            
class ConfMAA(object):
    def __init__(self, configsStation, ligne) -> None:
        super().__init__()
        infos = ligne.split('\t')
        #id		station	type		seuil	deroule		next_run			auto	pause
        #3260	FMEE	TS			1					2021-08-19 06:16:28	1		2
        self.station = infos[1]
        self.type_maa = infos[2]
        self.seuil = float(infos[3])
        self.auto = infos[6]=='1'
        self.pause = int(infos[7])
        try:
            self.scan = configsStation[self.station].__dict__['scan_'+self.type_maa]
            self.profondeur =  configsStation[self.station].__dict__['duree_'+self.type_maa ]
        except:
            pass
    
    def __str__(self):
        reponse = [ "{}: {}".format(key, value) for key, value in self.__dict__.items()]
        return "\n".join(reponse)

    @staticmethod
    def loadConfigs(fichier, configsStation):
        reponse = []
        with open(fichier, 'r') as ficin:
            ficin.readline()
            for ligne in ficin.readlines():
                if ligne.strip() != "":
                    config = ConfMAA(configsStation, ligne)
                    if config.station in configsStation.keys():
                        reponse.append(config)
        return reponse


class Command(BaseCommand):
    help = 'Initialise un environnement après supression de la base de données'

    """def add_arguments(self, parser):
        parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        for poll_id in options['poll_ids']:
            try:
                poll = Poll.objects.get(pk=poll_id)
            except Poll.DoesNotExist:
                raise CommandError('Poll "%s" does not exist' % poll_id)

            poll.opened = False
            poll.save()

            self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
            """
    
            

    def handle(self, *args, **options):
        
        # Suppression des régions existantes
        regions = Region.objects.all()
        for region in regions:
            region.delete()
        
        # Suppression des stations existantes
        stations = Station.objects.all()
        for station in stations:
            station.delete()
            """region = Region.objects.create(tag="DIRSE")
            self.stdout.write(self.style.SUCCESS('Create region DIRSE'))
            """

        # Lecture des configs station
        base_dir = Path(__file__).parent
        fichier_conf_station = base_dir.joinpath('config_station.csv')
        configs = ConfigsStation(fichier_conf_station)
        
        # Création des régions
        dirs = configs.get_dirs()
        dirs_objects = {}
        for dir in dirs:
            dirs_objects[dir] = Region.objects.create(tag=dir)

        # Création des stations
        for oaci, config in configs.stations.items():
            print (config.nom, config.station)

            Station.objects.create( oaci= oaci,
                                    nom = config.nom,
                                    entete = config.entete,
                                    date_pivot = config.date_pivot,
                                    region = dirs_objects[config.dir],
                                    active = True,
                                    ouverture = config.ouverture, ouverture1 = config.ouverture1, ouverture2 = config.ouverture2, 
                                    fermeture = config.fermeture, fermeture1 = config.fermeture1, fermeture2 = config.fermeture2, 
                                    retention = config.retention,
                                    reconduction = config.reconduction,
                                    repousse = config.delta_debut_repousse,
                                    wind_unit = config.unite_vent,
                                    temp_unit = config.unite_tempe,
                                    fuseau = config.fuseau,
                                    )

        # Création des groupes et permission
        groups = Group.objects.all()
        for group in groups:
            group.delete()
            

        configurateur, create = Group.objects.get_or_create(name="Configurateur")
        administrateur, create = Group.objects.get_or_create(name="Administrateur")
        superadmin, create = Group.objects.get_or_create(name="Super admin")
        
        # Droits sur Station
        content_Station = ContentType.objects.get_for_model(Station)
        configurateur.permissions.add(Permission.objects.get(codename='view_station', content_type=content_Station))
        configurateur.permissions.add(Permission.objects.get(codename='change_station', content_type=content_Station))
        
        superadmin.permissions.add(Permission.objects.get(codename='delete_station', content_type=content_Station))

        administrateur.permissions.add(Permission.objects.get(codename='add_station', content_type=content_Station))

        # Droits sur Région
        content_Region = ContentType.objects.get_for_model(Region)
        administrateur.permissions.add(Permission.objects.get(codename='view_region', content_type=content_Region))
        administrateur.permissions.add(Permission.objects.get(codename='change_region', content_type=content_Region))
        administrateur.permissions.add(Permission.objects.get(codename='add_region', content_type=content_Region))
        superadmin.permissions.add(Permission.objects.get(codename='delete_region', content_type=content_Region))

        # Droits sur Profil
        content_Region = ContentType.objects.get_for_model(Profile)
        content_User = ContentType.objects.get_for_model(User)

        administrateur.permissions.add(Permission.objects.get(codename='view_profile', content_type=content_Region))
        administrateur.permissions.add(Permission.objects.get(codename='view_user', content_type=content_User))
        administrateur.permissions.add(Permission.objects.get(codename='change_profile', content_type=content_Region))
        administrateur.permissions.add(Permission.objects.get(codename='change_user', content_type=content_User))
        administrateur.permissions.add(Permission.objects.get(codename='add_profile', content_type=content_Region))
        administrateur.permissions.add(Permission.objects.get(codename='add_user', content_type=content_User))

        superadmin.permissions.add(Permission.objects.get(codename='delete_profile', content_type=content_Region))
        superadmin.permissions.add(Permission.objects.get(codename='delete_user', content_type=content_User))


        # Droits sur les configMAA
        content_Region = ContentType.objects.get_for_model(ConfigMAA)

        configurateur.permissions.add(Permission.objects.get(codename='view_configmaa', content_type=content_Region))
        configurateur.permissions.add(Permission.objects.get(codename='change_configmaa', content_type=content_Region))
        configurateur.permissions.add(Permission.objects.get(codename='add_configmaa', content_type=content_Region))
        configurateur.permissions.add(Permission.objects.get(codename='delete_configmaa', content_type=content_Region))

        # Droits sur les envoi MAA
        envoi_maa = ContentType.objects.get_for_model(EnvoiMAA)

        configurateur.permissions.add(Permission.objects.get(codename='view_envoimaa', content_type=envoi_maa))
        
        """configurateur.permissions.add(Permission.objects.get(codename='add_envoimaa', content_type=envoi_maa))
        configurateur.permissions.add(Permission.objects.get(codename='change_envoimaa', content_type=envoi_maa))
        configurateur.permissions.add(Permission.objects.get(codename='delete_envoimaa', content_type=envoi_maa))
        """

        """permission, create = Permission.objects.get_or_create(codename='can_view', name='Can view station', content_type=content_Station)
        configurateur.permissions.add(permission)

        permission, create = Permission.objects.get_or_create(codename='can_delete', name='Can delete station', content_type=content_Station)
        superadmin.permissions.add(permission)

        permission, create = Permission.objects.get_or_create(codename='can_add', name='Can add station', content_type=content_Station)
        administrateur.permissions.add(permission)
        """


        # Création des profils
        users = User.objects.all()
        for user in users:
            if not user.is_superuser:
                user.delete()
            else:
                user.groups.add(administrateur)
                user.groups.add(configurateur)
                user.groups.add(superadmin)

        user = User.objects.create_user('administrateur', 'monique.le@meteo.fr', 'djangofr')
        user.is_staff = True
        user.profile.region = Region.objects.get(tag = "DIRN")
        user.groups.add(administrateur)
        user.groups.add(configurateur)
        user.save()

        user = User.objects.create_user('configurateur', 'config.le@meteo.fr', 'djangofr')
        user.is_staff = True
        user.profile.region = Region.objects.get(tag = "DIRN")
        user.groups.add(configurateur)
        user.save()

        #Profile.objects.create(user = user)
        
        # Charge les configs MAA depuis le fichier de confgi
        configsMAA = ConfigMAA.objects.all()
        for conf in configsMAA:
            conf.delete()
        
        fichier = base_dir.joinpath('table config_maa.csv')
        configs = ConfMAA.loadConfigs(fichier, configs.stations)

        t = []
        for conf in configs:
            station = Station.objects.get(oaci=conf.station)
            ConfigMAA.objects.create(
                station = station,
                type_maa = conf.type_maa,
                auto = conf.auto,
                seuil = conf.seuil,
                pause = conf.pause,
                scan = conf.scan,
                profondeur = conf.profondeur
            )
            t.append(conf.type_maa)
        
        #print(set(t))

        # implémente quelques envois de MAA
        envois = EnvoiMAA.objects.all()
        for envoi in envois:
            envoi.delete()
        
        conf_maa = ConfigMAA.objects.get(station__oaci = 'LFPG', type_maa= 'TS')
        envoi = EnvoiMAA.objects.create(
            configmaa = conf_maa,
            date_envoi = datetime.datetime.utcnow() - datetime.timedelta (hours= 3),
            date_debut = datetime.datetime.utcnow().replace(minute =0).replace(second=0) + datetime.timedelta (hours= 3),
            date_fin = datetime.datetime.utcnow().replace(minute =0).replace(second=0) + datetime.timedelta (hours= 8),
            numero = 1,
            fcst=True,
            status = 'to_send',
            message = """LFBT AD WRNG 1 VALID 201356/201500
TS OBS.
NO WARNING BEETWIN 00TU AND 04TU
=""",
            context_TAF = """LFPG,20180721230000,NSW,10000,10000,5,5,,18.2,,,0.0,0.0,0.1,0.4,0.6,0,0,0,20180720170000,0.0,300,0
LFPG,20180722000000,NSW,10000,10000,5,5,,17.4,,,0.0,0.0,0.0,0.3,0.6,0,0,0,20180720170000,0.0,300,0
LFPG,20180722030000,NSW,,,4,4,,15.9,14.9,,0.0,0.0,0.0,0.3,0.6,0,0,0,,0.0,360,
LFPG,20180722060000,NSW,,,2,2,,17.4,,,0.0,0.0,0.0,0.0,0.6,0,0,0,,0.0,-1,
LFPG,20180722090000,NSW,,,4,4,,22.7,,,0.0,0.0,0.0,0.0,0.6,0,0,0,,0.0,350,
LFPG,20180722120000,NSW,,,4,4,,26.1,,,0.0,0.0,0.0,0.0,0.3,0,0,0,,0.0,335,
LFPG,20180722150000,NSW,,,4,4,,27.3,,28.3,0.0,0.0,0.0,0.0,0.3,0,0,0,,0.0,10,
LFPG,20180722180000,NSW,,,6,6,,26.5,,,0.0,0.0,0.0,0.0,0.0,0,0,0,,0.0,35,""",

            log = "Ici, les logs de création",
            message_mail = 'Corps du mail',
            message_sms = "message SMS",
            
        )
        with open(base_dir.joinpath('MAAx.pdf'), 'rb') as f:
            envoi.message_pdf.save("MAA_LFPG_TS_1_20210824052410_1.pdf", File(f))
        print(envoi.message_pdf.path)

        clients = Client.objects.all()
        for client in clients:
            client.delete()
        mails = MediumMail.objects.all()
        for mail in mails:
            mail.delete()
        
        client = Client(
            nom = "Canova",
            prenom = "Philipp",
            telephone = "00000000",
            email = "philippe.canova@meteo.fr",
        )
        client.save()
        client.configmaas.add(conf_maa)

        dest_mail = MediumMail.objects.create(
            client = client,
            email = "ph.cano@free.fr"
        )