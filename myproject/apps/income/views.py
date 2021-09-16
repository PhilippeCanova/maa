import datetime

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from myproject.apps.core.models import ConfigMAA, EnvoiMAA


# Create your views here.
def SimpleView(request):
    
    if not request.GET or request.GET.get('usage', None) is not None:
        return HttpResponseBadRequest('Description du webservice.')    
    

    obligatoire = ['type_maa', 'station', 'seuil', 'date_debut', 'date_fin', 'fcst']
    for arg in obligatoire:
        if arg not in request.GET:
            return HttpResponseBadRequest("Le paramètre {} obligatoire.".format(arg) )

    station = request.GET.get('station', None)
    type_maa = request.GET.get('type_maa', None)
    seuil = request.GET.get('seuil', None)
    date_debut = request.GET.get('date_debut', None)
    date_fin = request.GET.get('date_fin', None)
    fcst = request.GET.get('fcst', None)
    
    # Vérficiation des champs :
    config = ConfigMAA.objects.filter(seuil=float(seuil)).filter(station__oaci=station).filter(type_maa=type_maa)

    if not config:
        return HttpResponseBadRequest("La combinaison station={} type={} seuil={} n'est pas connue.".format(station, type_maa, seuil) )
    
    if fcst.upper() not in ['FCST', 'OBS']:
        return HttpResponseBadRequest("Le caractère FCST doit prendre la valeur FCST ou OBS")
    
    try: 
        date_debut = datetime.datetime.strptime(date_debut,"%Y%m%d%H%M")
        date_fin = datetime.datetime.strptime(date_fin,"%Y%m%d%H%M")
    except:
        return HttpResponseBadRequest("Les paramètres date_debut et date_fin sont des dates. Ils doivent respecter le format AAAAMMDDhhmm.")
    
    if date_fin < date_debut:
        return HttpResponseBadRequest("La date de fin foit être postérieure à la date de début.")
    
    datejour = datetime.datetime.utcnow().replace(hour=0).replace(minute=0).replace(second=0).replace(microsecond=0)
    demain = datejour + datetime.timedelta(hours= 24)

    maas = EnvoiMAA.objects.filter(configmaa__station__oaci = station).filter(configmaa__type_maa=type_maa).filter(configmaa__seuil=seuil).filter(date_envoi__gt = datejour).filter(date_envoi__lt=demain).order_by('-date_envoi')
    numero = 0
    if len(maas)>0:
        numero = maas[0].numero
    numero = numero + 1
    
    nouveau_maa = EnvoiMAA(
        configmaa = config[0],
        date_envoi = datetime.datetime.utcnow(),
        date_debut = date_debut,
        date_fin = date_fin,
        numero = numero,
        log = "MAA créé par soumission via le webservice.",
        status = "to_send"
    )
    nouveau_maa.save()
    
    return HttpResponse('Nothing bad')