from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

class AutorisedMAA(object):
    def __init__(self, type, nom, **options):
        self.type = type
        self.nom = nom
        self.seuil = options.get('seuil', None)
        self.automatisable = options.get('auto', False)
        self.pause = options.get('pause', 2)
        self.scan =  options.get('scan', 12)
        self.profondeur =  options.get('profondeur', 12)
    

class AutorisedMAAs(object):
    autorised = [
        AutorisedMAA('TS', 'Orage', auto=True),
        AutorisedMAA('SQ', 'Grain', auto=False),
        AutorisedMAA('DENSE_FG', 'Brouillard dense', auto=False),
        
        AutorisedMAA('SN', 'SN', auto=False),
        AutorisedMAA('FZDZ', 'FZDZ', auto=False),
        AutorisedMAA('VENT_MOY', 'VENT_MOY', auto=False),
        AutorisedMAA('VEHICLE_RIME', 'VEHICLE_RIME ', auto=False),
        AutorisedMAA('TMIN', 'TMIN ', auto=False),
        AutorisedMAA('HVY_GR', 'HVY_GR ', auto=False),
        AutorisedMAA('TOXCHEM', 'TOXCHEM ', auto=False),
        AutorisedMAA('TC', 'TC ', auto=False),
        AutorisedMAA('DU', 'DU ', auto=False),
        AutorisedMAA('TMAX', 'TMAX ', auto=False),
        AutorisedMAA('HVY_SN', 'HVY_SN ', auto=False),
        AutorisedMAA('FG', 'FG ', auto=False),
        AutorisedMAA('HVY_TS', 'HVY_TS ', auto=False),
        AutorisedMAA('FWOID', 'FWOID ', auto=False),
        AutorisedMAA('ICE_DEPOSIT', 'ICE_DEPOSIT ', auto=False),
        AutorisedMAA('RR1', 'RR1 ', auto=False),
        AutorisedMAA('RR3', 'RR3 ', auto=False),
        AutorisedMAA('RR6', 'RR6 ', auto=False),
        AutorisedMAA('RR12', 'RR12 ', auto=False),
        AutorisedMAA('RR24', 'RR24 ', auto=False),
        AutorisedMAA('HVY_FZDZ', 'HVY_FZDZ ', auto=False),
        AutorisedMAA('FWID', 'FWID ', auto=False),
        AutorisedMAA('FZRA', 'FZRA ', auto=False),
        AutorisedMAA('GR', 'GR ', auto=False),
        AutorisedMAA('VENT', 'VENT ', auto=False),
        AutorisedMAA('RIME', 'RIME ', auto=False),
        AutorisedMAA('VA', 'VA ', auto=False),
        AutorisedMAA('HVY_FZRA', 'HVY_FZRA ', auto=False),
        AutorisedMAA('SNRA', 'SNRA ', auto=False),
        AutorisedMAA('SA', 'SA ', auto=False),
        AutorisedMAA('HVY_SNRA', 'HVY_SNRA ', auto=False),
        AutorisedMAA('SEA', 'SEA ', auto=False),
        AutorisedMAA('FZFG', 'FZFG ', auto=False),
        AutorisedMAA('BLSN', 'BLSN ', auto=False),
        AutorisedMAA('TSUNAMI', 'TSUNAMI ', auto=False),
        AutorisedMAA('HVY_SWELL', 'HVY_SWELL', auto=False),

        ]

    @staticmethod
    def get_choices()-> list:
        return [ (m.type, m.nom) for m in AutorisedMAAs.autorised ]

class Region(models.Model):
    """ Région météo regroupant les aéroport"""
    tag = models.TextField(max_length=10, null=False, unique=True, verbose_name="Tag région")

    def __str__(self):
        return self.tag



class Station(models.Model):
    """ Aéroport"""
    oaci = models.CharField(max_length=4, null=False, unique=True, verbose_name="Code OACI")
    nom = models.CharField(max_length=124, null=False, verbose_name="Nom")
    entete = models.CharField(max_length=11, null=False, verbose_name="Entete")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=False, blank=False, verbose_name="Dir")
    active = models.BooleanField(default = False)
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
        return "{} {} {} {} {} {} {}".format(self.station, self.type_maa, self.seuil, self.auto, self.pause, self.scan, self.profondeur)
 

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True)

class EnvoiMAA(models.Model):
    """ Liste des MAA générés/envoyés"""
    configmaa = models.ForeignKey(ConfigMAA, on_delete=models.CASCADE, null=False)
    date_envoi = models.DateTimeField(null=False)
    date_debut = models.DateTimeField(null=False)
    date_fin = models.DateTimeField(null=False)
    numero = models.IntegerField(null=False)
    message = models.TextField(null=False)
    context_TAF = models.TextField(null=True, blank=True)
    context_CDPH = models.TextField(null=True, blank=True)
    context_CDPQ = models.TextField(null=True, blank=True)
    log = models.TextField(null=True, blank=True)
    message_mail = models.TextField(null=True, blank=True)
    message_pdf = models.FileField(null=True, blank=True)
    message_sms = models.TextField(null=True, blank=True)


    def __str__(self):
        return "{} {} {} {}".format(self.configmaa.station.oaci, self.configmaa.type_maa, self.date_envoi, self.numero)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        print('create_user')
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    print('save_user')
    instance.profile.save()
