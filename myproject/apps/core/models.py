from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

TYPES_LOG = [
    ('error','Erreur'),
    ('warning','Avertissement'),
    ('info','Information'),
]
class AutorisedMAA(object):
    def __init__(self, type, nom, **options):
        self.type = type
        self.nom = nom
        self.seuil = options.get('seuil', None)
        self.automatisable = options.get('auto', False)
        self.pause = options.get('pause', 2)
        self.scan =  options.get('scan', 12)
        self.profondeur =  options.get('profondeur', 12)
        self.occurrence =  options.get('occurrence', True)

class AutorisedMAAs(object):
    autorised = {
        'TS':AutorisedMAA('TS', 'Orage', auto=True, occurrence=True),
        'SQ':AutorisedMAA('SQ', 'Grain', auto=False, occurrence=True),
        'DENSE_FG':AutorisedMAA('DENSE_FG', 'Brouillard dense', auto=False, occurrence=True), 
        'SN':AutorisedMAA('SN', 'SN', auto=False, occurrence=True),
        'FZDZ':AutorisedMAA('FZDZ', 'FZDZ', auto=False, occurrence=True),
        'VENT_MOY':AutorisedMAA('VENT_MOY', 'VENT_MOY', auto=False, occurrence=False),
        'VEHICLE_RIME':AutorisedMAA('VEHICLE_RIME', 'VEHICLE_RIME ', auto=False, occurrence=True),
        'TMIN':AutorisedMAA('TMIN', 'TMIN ', auto=False, occurrence=False),
        'HVY_GR':AutorisedMAA('HVY_GR', 'HVY_GR ', auto=False, occurrence=True),
        'TOXCHEM':AutorisedMAA('TOXCHEM', 'TOXCHEM ', auto=False, occurrence=True),
        'TC':AutorisedMAA('TC', 'TC ', auto=False, occurrence=True),
        'DU':AutorisedMAA('DU', 'DU ', auto=False, occurrence=True),
        'TMAX':AutorisedMAA('TMAX', 'TMAX ', auto=False, occurrence=False),
        'HVY_SN':AutorisedMAA('HVY_SN', 'HVY_SN ', auto=False, occurrence=True),
        'FG':AutorisedMAA('FG', 'FG ', auto=False, occurrence=True),
        'HVY_TS':AutorisedMAA('HVY_TS', 'HVY_TS ', auto=False, occurrence=True),
        'FWOID':AutorisedMAA('FWOID', 'FWOID ', auto=False, occurrence=True),
        'ICE_DEPOSIT':AutorisedMAA('ICE_DEPOSIT', 'ICE_DEPOSIT ', auto=False, occurrence=True),
        'RR1':AutorisedMAA('RR1', 'RR1 ', auto=False, occurrence=False),
        'RR3':AutorisedMAA('RR3', 'RR3 ', auto=False, occurrence=False),
        'RR6':AutorisedMAA('RR6', 'RR6 ', auto=False, occurrence=False),
        'RR12':AutorisedMAA('RR12', 'RR12 ', auto=False, occurrence=False),
        'RR24':AutorisedMAA('RR24', 'RR24 ', auto=False, occurrence=False),
        'HVY_FZDZ':AutorisedMAA('HVY_FZDZ', 'HVY_FZDZ ', auto=False, occurrence=True),
        'FWID':AutorisedMAA('FWID', 'FWID ', auto=False, occurrence=True),
        'FZRA':AutorisedMAA('FZRA', 'FZRA ', auto=False, occurrence=True),
        'GR':AutorisedMAA('GR', 'GR ', auto=False, occurrence=True),
        'VENT':AutorisedMAA('VENT', 'VENT ', auto=False, occurrence=False),
        'RIME':AutorisedMAA('RIME', 'RIME ', auto=False, occurrence=True),
        'VA':AutorisedMAA('VA', 'VA ', auto=False, occurrence=True),
        'HVY_FZRA':AutorisedMAA('HVY_FZRA', 'HVY_FZRA ', auto=False, occurrence=True),
        'SNRA':AutorisedMAA('SNRA', 'SNRA ', auto=False, occurrence=True),
        'SA':AutorisedMAA('SA', 'SA ', auto=False, occurrence=True),
        'HVY_SNRA':AutorisedMAA('HVY_SNRA', 'HVY_SNRA ', auto=False, occurrence=True),
        'SEA':AutorisedMAA('SEA', 'SEA ', auto=False, occurrence=True),
        'FZFG':AutorisedMAA('FZFG', 'FZFG ', auto=False, occurrence=True),
        'BLSN':AutorisedMAA('BLSN', 'BLSN ', auto=False, occurrence=True),
        'TSUNAMI':AutorisedMAA('TSUNAMI', 'TSUNAMI ', auto=False, occurrence=True),
        'HVY_SWELL':AutorisedMAA('HVY_SWELL', 'HVY_SWELL', auto=False, occurrence=True),
    }

    @staticmethod
    def get_choices()-> list:
        reponse = [ (m.type, m.nom) for key, m in AutorisedMAAs.autorised.items() ]
        return sorted(reponse)
    @staticmethod
    def is_occurrence(type_maa)-> bool:
        return AutorisedMAAs.autorised[type_maa].occurrence == True

    @staticmethod
    def is_automatisable(type_maa)-> bool:
        return AutorisedMAAs.autorised[type_maa].automatisable == True

class Region(models.Model):
    """ Région météo regroupant les aéroport"""
    tag = models.TextField(max_length=10, null=False, unique=True, verbose_name="Tag région")

    def __str__(self):
        return self.tag

class Log(models.Model):
    """ Stoque les logs que l'on veut faire remonter """
    heure = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=10, null=False, choices= TYPES_LOG)
    machine = models.CharField(max_length=20, null=False) # Indique le nom de la machine ayant lancé le log
    code = models.CharField(max_length = 8)
    message = models.TextField(null=False)

    def __str__(self):
        return "{}-{}-{}-{}-{}".format(self.heure, self.type, self.machine, self.code, self.message)
class Station(models.Model):
    """ Aéroport"""
    oaci = models.CharField(max_length=4, null=False, unique=True, verbose_name="Code OACI")
    nom = models.CharField(max_length=124, null=False, verbose_name="Nom")
    entete = models.CharField(max_length=11, null=False, verbose_name="Entete")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=False, blank=False, verbose_name="Dir")
    active = models.BooleanField(default = False)
    inseepp = models.CharField(max_length=7, null=False, verbose_name="INSEEpp")
    outremer = models.BooleanField(default= False, null=False)
    date_pivot = models.DateTimeField(null=False, verbose_name="Date changement d'heure")
    ouverture = models.TimeField(null=False, verbose_name="H ouverture")
    ouverture1 = models.TimeField(null=False, verbose_name="H ouverture avant pivot")
    ouverture2 = models.TimeField(null=False, verbose_name="H ouverture après pivot")
    fermeture = models.TimeField(null=False, verbose_name="H fermeture")
    fermeture1 = models.TimeField(null=False, verbose_name="H fermeture avant pivot")
    fermeture2 = models.TimeField(null=False, verbose_name="H fermeture après pivot")
    retention = models.IntegerField(null=False)
    reconduction = models.IntegerField(null=False)
    repousse = models.IntegerField(null=False)
    fuseau = models.CharField(max_length=124, null=False)
    wind_unit = models.CharField(max_length=3, null=False, choices=[('kt','kt'), ('kmh','km/h')], verbose_name="Unité de vitesse")
    temp_unit = models.CharField(max_length=3, null=False, choices=[('c',"°C"), ('f',"F")], verbose_name="Unité de température")

    def __str__(self):
        return "{}- {} ({})".format(self.oaci, self.nom, self.region)
class ConfigMAA(models.Model):
    """ Liste les MAA autorisés pour une station"""
    station = models.ForeignKey(Station, on_delete=models.CASCADE, null=False)
    type_maa = models.CharField(max_length=20, null=False, choices= AutorisedMAAs.get_choices())
    seuil = models.FloatField(null=True, blank=True)
    auto = models.BooleanField(null=False, default= False)
    pause = models.IntegerField(null=False, default=2)
    scan = models.IntegerField(null=False, default=12)
    profondeur = models.IntegerField(null=False, default=12)

    def __str__(self):
        reponse = "{} - {}".format(self.station, self.type_maa)
        if not AutorisedMAAs.is_occurrence(self.type_maa):
            # Ajout du seuil si le maa n'est pas de type occurrence
            reponse = reponse + " - {}".format(self.seuil)
        reponse = reponse + " ({} {} {} {})".format(self.auto, self.pause, self.scan, self.profondeur)

        return reponse
    
    class Meta:
        ordering = ["station", "type_maa", "seuil"]
    
        

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True)

class EnvoiMAA(models.Model):
    """ Liste des MAA générés/envoyés"""

    # Détermine les différents statuts possibles pour un MAA généré en base.
    CHOICES_STATUS = [
        ('to_send', 'Nouveau'), # A envoyer
        ('submit', 'Edité'),    # Envoyé à difmet avec retour OK du ftp 
        ('ok', 'Envoyé'),       # Acquittement de délivrance de Difmet
    ]

    configmaa = models.ForeignKey(ConfigMAA, on_delete=models.CASCADE, null=False)
    date_envoi = models.DateTimeField(null=False)
    date_debut = models.DateTimeField(null=False)
    date_fin = models.DateTimeField(null=False)
    numero = models.IntegerField(null=False)
    message = models.TextField(null=False)
    fcst = models.BooleanField(null=False, default=True)
    status = models.CharField(max_length=10, editable=False, null=False, default='new', choices = CHOICES_STATUS)
    context_TAF = models.TextField(null=True, blank=True)
    context_CDPH = models.TextField(null=True, blank=True)
    context_CDPQ = models.TextField(null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    message_mail = models.TextField(null=True, blank=True)
    message_pdf = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    message_sms = models.TextField(null=True, blank=True)


    def __str__(self):
        return "{} {} {} {}".format(self.configmaa.station.oaci, self.configmaa.type_maa, self.date_envoi, self.numero)

class Client(models.Model):
    """ Liste des destinataires reconnus"""
    nom = models.CharField(max_length= 250, null=False)
    prenom = models.CharField(max_length= 250, null=True, blank=True)
    telephone = models.CharField(max_length= 15, null=False)
    email = models.EmailField(max_length= 250, null=True, blank=True)
    configmaas = models.ManyToManyField(ConfigMAA)
    
    def __str__(self):
        return "{} {} {} {}".format(self.nom, self.prenom, self.telephone, self.email)


class MediumMail(models.Model):
    """ Destinataires d'un client donnée"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=False)
    email = models.EmailField( null=False)

class MediumSMS(models.Model):
    """ Destinataires d'un client donnée"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=False)
    sms = models.CharField(max_length=15, null=False)
    
class MediumFTP(models.Model):
    """ Destinataires d'un client donnée"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=False)
    remote = models.CharField(max_length=254, null=False)
    login = models.CharField(max_length=254, null=False)
    pwd = models.CharField(max_length=254, null=False)
    dir = models.CharField(max_length=254, null=True, blank=True)
    



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        #print('create_user')
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    #print('save_user')
    instance.profile.save()
