"""
    Module permettant de rassembler les fonctions nécessaires pour la recherche des MAA potentiels et la livraison de ceux-ci. 

    A chaque analyse de 15 mn, il faut :
        - récupérer les stations actives et leur configuration
        - lancer une récupération des données
        - définir sur quelles stations il faut faire l'analyse (arrêt de certaines surveillance la nuit)
        - définir les MAA potentiels
        - récupérer les MAA en cours de validité
        - le cas échéant, générer un nouveau MAA  
"""
from datetime import datetime, time, timedelta

from configurateur.models import Station, ConfigMAA
from analyseur.models import EnvoiMAA
from configurateur.utils import chek_and_change_pivot_date
from analyseur.models import EnvoiMAA
from donneur.commons import provide_manager

def define_open_airport(NOW):
    """ Définit les stations sur lesquelles la production est actuellement assurée (injustement appelées ouvertes) 
        Retourne le queryset de ces stations.
    """
    # Cet arrondi assure que les stations fermant à 23:59 (donc non fermant) soit bien considérée ouverte
    heure = datetime.time(NOW).replace(second=0).replace(microsecond=0) 
    
    stations = Station.objects.filter(active = True).filter(ouverture__lte = heure).filter(fermeture__gte = heure)
    
    return stations

def define_start_laptime(heure_analyse, configmaa):
    """ Recherche la période durant laquelle on autorise le départ d'un éventuel MAA. 
        Cette période dépend de l'heure d'analyse et du paramètre scan du configmaa.

        Retourne une liste de datetime par pas de 1h dans la période de recherche.
    """
    # arrondi à l'heure précédente
    reseau_analyse = heure_analyse.replace(minute = 0).replace(second=0).replace(microsecond=0) 

    # Paramètre dépendant de la config (généralement 12h)
    scan = configmaa.scan

    reseaux_recherche = []
    for i in range(0, scan+1):
        reseaux_recherche.append( reseau_analyse + timedelta(hours=i) )

    return reseaux_recherche

def recherche_debut_maa(assembleur, oaci, periode_debut, configmaa):
    """ Sur la période acceptable de début MAA, on cherche s'il y a une heure déclenchante pour le type de MAA donné 
        Retourne le datetime du premier déclenchement ou None si rien trouvé.
    """
    for echeance in periode_debut:
        if assembleur.question_declenche(oaci, echeance, configmaa.type_maa, configmaa.seuil):
            return echeance
    return None

def delai_retention_depasse(heure_actuelle, envoimaa):
    """ Permet de définir si le délai légal de rétention d'un maa envoyé est déjà dépassé 
        Cette limite dépend de la station (et du paramètre retention)
        Retourne True si le délai est dépassé.
    """
    retention = envoimaa.configmaa.station.retention
    return heure_actuelle > envoimaa.date_envoi + timedelta(hours = retention)

def bientot_fini(heure_actuelle, envoimaa):
    """ Retourne True si le maa passé "envoimaa" se termine dans moins d'une heure """
    return heure_actuelle > envoimaa.date_fin - timedelta(hours=1)

def recherche_fin_maa(assembleur, oaci, heure_debut_declenche, configmaa):
    """ On a trouvé une heure de début de maa dans la période acceptable.
        On cherche à présent une heure de fin dans l'intervalle autorisé.
        Au maximum, le MAA s'arrête à heure début + profondeur (paramètre lié à la confi maa)
        S'il y a une interruption de plus de {Pause} heures, on considère le MAA terminé
        Retourne cette heure, ou à défaut au moins l'heure de début 
    """
    heure_fin_max = heure_debut_declenche + configmaa.profondeur
    echeances = [ heure_debut_declenche + timedelta(hours=i) for i in range(0, configmaa.profondeur)]
    pause = 0
    for echeance in echeances:
        if assembleur.question_declenche(oaci, echeance, configmaa.type_maa, configmaa.seuil):
            pause = 0
        else:
            pause = pause + 1
            if pause > configmaa.pause:
                break
    return echeance

def analyse_15mn(heure_analyse=datetime.utcnow()):

    # Met à jour les heures d'ouverture et de fermeture
    chek_and_change_pivot_date() 

    # Récupère la liste des stations en cours de production
    stations = define_open_airport(heure_analyse)

    manager_cdp = provide_manager(stations)

    # Parmi les stations en cours d'exploitation, détermine les MAA automatique à analyser
    for station in stations:
        # Récupère les Config de MAA auto à tester.
        configmaa_to_check = ConfigMAA.objects.filter(station__oaci = station.oaci).filter(auto = True)

        for configmaa in configmaa_to_check:
            # Récupère le MAA déjà en cours s'il y en a un
            maa_en_cours = EnvoiMAA.objects.current_maas_by_type(station.oaci, configmaa.type_maa, heure_analyse, configmaa.seuil)

            # Période de recherche du début d'un éventuel MAA
            periode_debut = define_start_laptime(heure_analyse, configmaa)

            heure_debut_declenche = recherche_debut_maa(manager_cdp, station.oaci, periode_debut, configmaa)
        
            if heure_debut_declenche is None:
                # Pas de MAA en vue
                # S'il y a un MAA en cours, qu'on a passé la limite de rétention, et qu'il finit dans plus d'une heure, on doit le cancellé
                # sinon on ne fait rien"""
                if maa_en_cours is not None and delai_retention_depasse(heure_analyse, maa_en_cours):
                    if bientot_fini(heure_analyse, maa_en_cours):
                        #TODO: il faut générer une anulation de MAA
                        pass

                # Plus rien à faire si pas de MAA en vue, donc on peut passer à la boucle suivante
                continue

            # A ce stade, il y a un MAA potentiel à venir (car heure de déclenchement). 
            # Il faut déterminer à sa date de fin de validité potentielle
            heure_fin_potentielle = recherche_fin_maa(manager_cdp, station.oaci, heure_debut_declenche, configmaa)
            #TODO: tester la recherche potentielle d'heure de fin. 

            # On a donc maintenant un MAA en cours et un MAA potentiel. On va faire une suite de tests permettant
            # de savoir s'il y a opportunité d'envoyer un nouveau MAA. (cf spec DP-8)
                       

    

    



