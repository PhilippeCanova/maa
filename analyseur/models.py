import datetime

from django.db import models
from django.db.models.query import QuerySet

from myproject.models.mes_mixins import Activable
from configurateur.models import ConfigMAA


# Create your models here.

class EnvoiMAAQuerySet(QuerySet):
    """ Permet de définir un manager particulier et d'accès plus simplement à certaines requêtes """
    #TODO: voir pour être sûr de n'avoir que le plus récent
    def current_maas(self):
        """ Permet de retourner tous les maa en cours 
            Attention, plusieurs peuvent être retournés pour un même type
        """
        return self.filter(date_fin__gt = datetime.datetime.utcnow()).order_by('-date_envoi')
    
    def current_maas_by_station(self, oaci, heure= datetime.datetime.utcnow()):
        """ Permet de retourner les maa en cours pour une station {oaci} donnée 
            Attention, plusieurs peuvent être retournés
        """
        return self.filter(date_fin__gt = heure).filter(configmaa__station__oaci = oaci).order_by('-date_envoi')
    
    def current_maas_by_type(self, oaci, type_maa, heure= datetime.datetime.utcnow(), seuil=None):
        """ Permet de retourner le dernier MAA en cours de validité pour un type données 
            C'est donc une instance de EnvoiMAA s'il y en a un, ou None sinon """
        selon_seuil = self.filter(date_fin__gt = heure).filter(configmaa__station__oaci = oaci)
        selon_seuil = selon_seuil.filter(configmaa__type_maa = type_maa).order_by('-date_envoi')
        if seuil is not None:
            selon_seuil = selon_seuil.filter(configmaa__seuil = seuil)        
        return selon_seuil.first()
    
    def history_maas(self, nb_heures = 48, maintenant = datetime.datetime.utcnow()):
        """ Permet de retourner la liste des maa envoyés au cours de {nb_heures} dernières heures """
        avant = maintenant - datetime.timedelta(hours=nb_heures)
        return self.filter(date_envoi__gt = avant)

class EnvoiMAA(models.Model):
    """ Liste des MAA générés/envoyés"""

    # Détermine les différents statuts possibles pour un MAA généré en base.
    CHOICES_STATUS = [
        ('to_send', 'Nouveau'), # A envoyer
        ('submit', 'Edité'),    # Envoyé à difmet avec retour OK du ftp 
        ('ok', 'Envoyé'),       # Acquittement de délivrance de Difmet
    ]

    objects = EnvoiMAAQuerySet.as_manager()
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
