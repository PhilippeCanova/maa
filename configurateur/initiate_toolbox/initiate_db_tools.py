from pathlib import Path
import datetime
import time

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from myproject.apps.core.models import Log
from analyseur.models import EnvoiMAA
from profiles.models import Profile
from configurateur.models import Region, Station, ConfigMAA, Client, MediumMail, AutorisedMAAs

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
                    config.ouverture_ete = datetime.datetime.strptime(config.ouverture1, "%H:%M")
                    config.ouverture_hiver = datetime.datetime.strptime(config.ouverture2, "%H:%M")
                    if config.fermeture == '24:00': config.fermeture = '23:59'
                    if config.fermeture1 == '24:00': config.fermeture1 = '23:59'
                    if config.fermeture2 == '24:00': config.fermeture2 = '23:59'
                    config.fermeture = datetime.datetime.strptime(config.fermeture, "%H:%M")
                    config.fermeture_ete = datetime.datetime.strptime(config.fermeture1, "%H:%M")
                    config.fermeture_hiver = datetime.datetime.strptime(config.fermeture2, "%H:%M")
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

class Initiate(object):
    """ Cette classe permet de préparer la base de donnée en fonction des besoins :
            - initialisation de la base oper lors de la migration ou des tests d'intégration
            - lancement des tests

        Les outils principaux sont découpés comme suit :
            - une fonciton delete qui remet à zéro la base. 
            - ... à détailler ...
    """
    def delete(self):
        # Suppression des régions existantes
        regions = Region.objects.all()
        for region in regions:
            region.delete()
        
        # Suppression des stations existantes
        stations = Station.objects.all()
        for station in stations:
            station.delete()

        # Création des groupes et permission
        groups = Group.objects.all()
        for group in groups:
            group.delete()
        
        # Charge les configs MAA depuis le fichier de confgi
        configsMAA = ConfigMAA.objects.all()
        for conf in configsMAA:
            conf.delete()

        # implémente quelques envois de MAA
        envois = EnvoiMAA.objects.all()
        for envoi in envois:
            envoi.delete()

        clients = Client.objects.all()
        for client in clients:
            client.delete()

        mails = MediumMail.objects.all()
        for mail in mails:
            mail.delete()

        # Création des profils
        users = User.objects.all()
        for user in users:
            #if not user.is_superuser:
            user.delete()

        content_ConfiMAA = ContentType.objects.get_for_model(ConfigMAA)
        try:
            expert = Permission.objects.get(codename = 'expert_configmaa', content_type=content_ConfiMAA)
            expert.delete()
        except:
            pass

    def create(self):
        # Lecture des configs station
        base_dir = Path(__file__).parent.joinpath('box_oper')
        fichier_conf_station = base_dir.joinpath('config_station.csv')

        configs = ConfigsStation(fichier_conf_station)

        # Lecture des correspondances OACI - insee
        fichier_correspondance = base_dir.joinpath('correspondanceMAA.csv')
        correspondance = {}
        with open(fichier_correspondance, 'r') as ficin:
            for ligne in ficin.readlines():
                infos = ligne.split(';')
                correspondance[infos[1].strip()] = infos[0]
        
        # Création des régions
        dirs = configs.get_dirs()
        dirs_objects = {}
        for dir in dirs:
            dirs_objects[dir] = Region.objects.create(tag=dir)

        # Création des stations
        for oaci, config in configs.stations.items():
            if oaci in correspondance.keys():
                inseepp = correspondance[oaci]
                outremer = False
                if inseepp[:2] > '95':
                    outremer = True
                Station.objects.create( oaci= oaci,
                                    nom = config.nom,
                                    entete = config.entete,
                                    date_pivot = config.date_pivot,
                                    region = dirs_objects[config.dir],
                                    inseepp = inseepp,
                                    outremer = outremer,
                                    active = True,
                                    ouverture = config.ouverture, ouverture_ete = config.ouverture_ete, ouverture_hiver = config.ouverture_hiver, 
                                    fermeture = config.fermeture, fermeture_ete = config.fermeture_ete, fermeture_hiver = config.fermeture_hiver, 
                                    retention = config.retention,
                                    reconduction = config.reconduction,
                                    repousse = config.delta_debut_repousse,
                                    wind_unit = config.unite_vent,
                                    temp_unit = config.unite_tempe,
                                    fuseau = config.fuseau,
                                    )
            else:
                print ("Station sans correspondance OACI-inseepp", oaci)

        
        configurateur, create = Group.objects.get_or_create(name="Configurateur")
        administrateur, create = Group.objects.get_or_create(name="Administrateur")
        superadmin, create = Group.objects.get_or_create(name="Super admin")
        maa_manuel, create = Group.objects.get_or_create(name="Editeur manuel")
        
        
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
        content_ConfiMAA = ContentType.objects.get_for_model(ConfigMAA)
        # => crée une autorisation de modifier les paramètres fins des config MAA
        change_fin, nope = Permission.objects.get_or_create(codename = 'expert_configmaa', name="Can specify configMAA", content_type=content_ConfiMAA)
        administrateur.permissions.add(change_fin)
        superadmin.permissions.add(change_fin)

        configurateur.permissions.add(Permission.objects.get(codename='view_configmaa', content_type=content_ConfiMAA))
        configurateur.permissions.add(Permission.objects.get(codename='change_configmaa', content_type=content_ConfiMAA))
        configurateur.permissions.add(Permission.objects.get(codename='add_configmaa', content_type=content_ConfiMAA))
        configurateur.permissions.add(Permission.objects.get(codename='delete_configmaa', content_type=content_ConfiMAA))


        # Droits sur les envoi MAA
        envoi_maa = ContentType.objects.get_for_model(EnvoiMAA)
        configurateur.permissions.add(Permission.objects.get(codename='view_envoimaa', content_type=envoi_maa))
        # Créé un droit particulier pour éditer des maa manuels
        edit_manuel, nope = Permission.objects.get_or_create(codename = 'envoimaa_manuel', name="Can Send manual MAA", content_type=envoi_maa)
        maa_manuel.permissions.add(edit_manuel)
        
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
            if user.is_superuser:
                user.groups.add(administrateur)
                user.groups.add(configurateur)
                user.groups.add(superadmin)
        # Pour la création du superuser, on doit pouvoir passer par :
        #from django.contrib.auth import get_user_model
        #get_user_model().objects.create_superuser
        user = User.objects.create_superuser('philippe', 'philippe.canova@meteo.fr', 'fr')
        user.is_staff = True
        #user.profile.region = Region.objects.get(tag = "DIRN")
        user.groups.add(superadmin)
        user.groups.add(administrateur)
        user.groups.add(configurateur)
        user.save()


        user = User.objects.create_user('administrateur', 'monique.le@meteo.fr', 'djangofr')
        user.is_staff = True
        user.profile.region = Region.objects.get(tag = "DIRN")
        user.groups.add(administrateur)
        user.groups.add(configurateur)
        user.save()

        user = User.objects.create_user('expair', 'expair.le@meteo.fr', 'expair')
        user.is_staff = False
        user.groups.add(maa_manuel)
        user.save()

        user = User.objects.create_user('configurateur', 'config.le@meteo.fr', 'djangofr')
        user.is_staff = True
        user.profile.region = Region.objects.get(tag = "DIRN")
        user.groups.add(configurateur)
        user.save()
        
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
        
        conf_maa = ConfigMAA.objects.get(station__oaci = 'LFPG', type_maa= 'TS')
        envoi = EnvoiMAA.objects.create(
            configmaa = conf_maa,
            date_envoi = datetime.datetime.utcnow() - datetime.timedelta (hours= 3),
            date_debut = datetime.datetime.utcnow().replace(minute =0).replace(second=0) + datetime.timedelta (hours= 3),
            date_fin = datetime.datetime.utcnow().replace(minute =0).replace(second=0) + datetime.timedelta (hours= 8),
            numero = 1,
            fcst="FCST",
            status = 'to_send',
            message = """LFBT AD WRNG 1 VALID 201356/201500\nTS OBS.\nNO WARNING BEETWIN 00TU AND 04TU\n=""",
            context_TAF = """context""",

            log = "Ici, les logs de création",
            message_mail = 'Corps du mail',
            message_sms = "message SMS",
            
        )
        #with open(base_dir.joinpath('MAAx.pdf'), 'rb') as f:
        #    envoi.message_pdf.save("MAA_LFPG_TS_1_20210824052410_1.pdf", File(f))
        
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

        # Crée un log :
        log = Log(
            type = 'error',
            machine = settings.MACHINE,
            code = '000',
            message = 'Initiate'
        )
        log.save()

    def check_ressource(self, path):
        """ Fait la vérification d'usage pour le fichier """
        path_file = self.box.joinpath(path)
        if not path_file.exists():
            raise FileExistsError("Le chemin {} n'existe pas. Les données ne peuvent pas être initialisées.".format(path_file))
        
    def __init__(self, box="box_test"):
        """ box nomme le répertoire contenant les fichiers configuration à installer """
        rep = Path(__file__).parent
        self.box = rep.joinpath(box)
        self.check_ressource(self.box)

        #TODO: prévoir aussi la création d'instance EnvoiMAA basiques et spécifiques
    
    def create_all_base_test(self):
        """ Instancie toutes les tables en une seule commande """
        from configurateur.initiate_toolbox.initiate_db_tools import Initiate
        self.create_region()
        self.create_group_and_permissions()
        self.create_users()
        self.create_stations()
        self.create_full_configmaa()

    def create_region(self, fichier="liste_regions.csv"):
        """ Crée les objets Region """
        path_file = self.box.joinpath(fichier)
        self.check_ressource(path_file)

        with open(path_file, 'r') as ficin:
            for ligne in ficin.readlines():
                ligne = ligne.strip()
                if ligne != "":
                    Region.objects.create(tag=ligne)

    def create_group_and_permissions(self):
        # Création des groupes
        configurateur, create = Group.objects.get_or_create(name="Configurateur")
        administrateur, create = Group.objects.get_or_create(name="Administrateur")
        superadmin, create = Group.objects.get_or_create(name="Super admin")
        maa_manuel, create = Group.objects.get_or_create(name="Editeur manuel")
        
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
        content_ConfiMAA = ContentType.objects.get_for_model(ConfigMAA)
        # => crée une autorisation de modifier les paramètres fins des config MAA
        change_fin, nope = Permission.objects.get_or_create(codename = 'expert_configmaa', name="Can specify configMAA", content_type=content_ConfiMAA)
        administrateur.permissions.add(change_fin)
        
        superadmin.permissions.add(change_fin)

        configurateur.permissions.add(Permission.objects.get(codename='view_configmaa', content_type=content_ConfiMAA))
        configurateur.permissions.add(Permission.objects.get(codename='change_configmaa', content_type=content_ConfiMAA))
        configurateur.permissions.add(Permission.objects.get(codename='add_configmaa', content_type=content_ConfiMAA))
        configurateur.permissions.add(Permission.objects.get(codename='delete_configmaa', content_type=content_ConfiMAA))


        # Droits sur les envoi MAA
        envoi_maa = ContentType.objects.get_for_model(EnvoiMAA)
        configurateur.permissions.add(Permission.objects.get(codename='view_envoimaa', content_type=envoi_maa))
        # Créé un droit particulier pour éditer des maa manuels
        edit_manuel, nope = Permission.objects.get_or_create(codename = 'envoimaa_manuel', name="Can Send manual MAA", content_type=envoi_maa)
        maa_manuel.permissions.add(edit_manuel)

    def create_users(self, fichier="liste_utilisateurs.csv"):
        """ Crée les utilisateurs """
        path_file = self.box.joinpath(fichier)
        self.check_ressource(path_file)

        groupes = {}
        for tag in ['Super admin', 'Administrateur', 'Configurateur', 'Editeur manuel']:
            groupes[tag] = Group.objects.get(name=tag)

        with open(path_file, 'r') as ficin:
            # pseudo;mail;pwd;is_superadmin;is_taf;tag_region;liste/groupes
            ficin.readline()
            for ligne in ficin.readlines():
                if ligne.strip() == '':
                    continue
                infos = ligne.strip().split(";")
                login = infos[0]
                email = infos[1]
                pwd = infos[2]
                is_admin = bool(infos[3])
                is_staff = bool(infos[4])
                tag_region = infos[5]
                liste_groupes = infos[6].split("/")

                if is_admin:
                    # Pour la création du superuser, on doit pouvoir passer par :
                    #from django.contrib.auth import get_user_model
                    #get_user_model().objects.create_superuser
                    user = User.objects.create_superuser(login, email, pwd)
                    user.is_staff = is_staff
                else:
                    user.is_staff = True
                    user = User.objects.create_user(login, email, pwd)
                
                user.is_staff = is_staff
                if tag_region != "": 
                    user.profile.region = Region.objects.get(tag = tag_region)

                #Affecte un groupe
                for groupe in liste_groupes:
                    user.groups.add(groupes[groupe])
                user.save()

    def create_stations(self, fichier="liste_stations.csv"):
        """ Configure les stations """
        path_file = self.box.joinpath(fichier)
        self.check_ressource(path_file)

        with open(path_file, 'r') as ficin:

            # oaci;nom;entete;date_pivot;region__tag;inseepp;outremer;active;ouverture;fermeture;retention;reconduction;repousse;wint_unit;fuseau
            ficin.readline() # Evince la première ligne
            
            for ligne in ficin.readlines():
                if ligne.strip() == '':
                    continue
                infos = ligne.strip().split(";")

                oaci= infos[0]
                nom = infos[1]
                entete = infos[2]
                date_pivot = datetime.datetime.strptime(infos[3], "%Y-%m-%d %H:%M:%S")
                region = Region.objects.get(tag=infos[4])
                inseepp = infos[5]
                outremer = infos[6]=='True'
                active = infos[7]=='True'
                ouverture = infos[8]
                fermeture = infos[9]
                retention = int(infos[10])
                reconduction = int(infos[11])
                repousse = int(infos[12])
                wind_unit = infos[13]
                fuseau = infos[14]
                ouverture_hiver = infos[15]
                fermeture_hiver = infos[16]
                ouverture_ete = infos[17]
                fermeture_ete = infos[18]

                station= Station.objects.create(
                    oaci = oaci, nom=nom, entete=entete, date_pivot=date_pivot,
                    region=region, inseepp=inseepp, outremer=outremer, active=active, 
                    ouverture=ouverture, fermeture=fermeture, retention=retention, reconduction=reconduction,
                    repousse=repousse, wind_unit=wind_unit, fuseau = fuseau, 
                    ouverture_hiver = ouverture_hiver, fermeture_hiver = fermeture_hiver,
                    ouverture_ete = ouverture_ete, fermeture_ete = fermeture_ete
                    )

    def create_configmaa(self, oaci, types = ['VENT', 'TMIN', 'TS']):
        """ Crée un set de config MAA pour une station oaci en fonction des types passés en paramètres
            Par défaut, pause = 2, scan = 3 pour GR, TS et 12 pour les autres, profondeur = 12
            Les maa automatisable sont mis à auto

        """
        station = Station.objects.get(oaci = oaci)
        pause = 2
        scan = 12
        profondeur = 12
        for type_maa in types:
            if type_maa in ['GR', 'TS']: scan = 3
            default_maa = AutorisedMAAs.get_instance(type_maa)
            auto = default_maa.automatisable

            if not default_maa.occurrence:
                seuil = 10
            else:
                seuil = None
            ConfigMAA.objects.create(
                station = station, type_maa = type_maa, seuil = seuil,
                auto = auto, pause = pause, scan = scan, profondeur = profondeur)
    
    def create_full_configmaa(self):
        """ Crée l'ensemble des MAA possibles pour l'ensemble des stations exitantes """
        stations = Station.objects.all()
        all_types = [ type_maa for type_maa, label in AutorisedMAAs.get_choices()]
        for station in stations:
            self.create_configmaa(station.oaci, all_types)
