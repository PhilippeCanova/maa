from django.shortcuts import render
import json
from datetime import datetime

from django.views.generic import DetailView
from analyseur.models import EnvoiMAA

# Create your views here.
class ProductMAA(DetailView):
    model = EnvoiMAA
    template_name = "producteur/product_maa_detail.html"

    """
    Pour test avec vent :
    [["2021-11-26 10:00:00", [10, 15, 300]], ["2021-11-26 11:00:00", [10, 10, 300]], ["2021-11-26 12:00:00", [10, 10, 300]], ["2021-11-26 13:00:00", [10, 15, 300]], ["2021-11-26 14:00:00", [10, 20, 300]], ["2021-11-26 15:00:00", [10, 25, 300]], ["2021-11-26 16:00:00", [10, 15, 300]], ["2021-11-26 17:00:00", [10, 15, 300]], ["2021-11-26 18:00:00", [10, 15, 300]], ["2021-11-26 19:00:00", [10, 15, 300]], ["2021-11-26 20:00:00", [10, 15, 300]], ["2021-11-26 21:00:00", [10, 15, 300]], ["2021-11-26 22:00:00", [10, 15, 300]], ["2021-11-26 23:00:00", [10, 15, 300]], ["2021-11-27 00:00:00", [10, 15, 300]], ["2021-11-27 01:00:00", [10, 15, 300]], ["2021-11-27 02:00:00", [10, 15, 300]], ["2021-11-27 03:00:00", [10, 15, 300]], ["2021-11-27 04:00:00", [10, 15, 300]], ["2021-11-27 05:00:00", [10, 15, 300]], ["2021-11-27 06:00:00", [10, 15, 300]], ["2021-11-27 07:00:00", [10, 15, 300]], ["2021-11-27 08:00:00", [10, 15, 300]], ["2021-11-27 09:00:00", [10, 15, 300]]]

    Pour test avec température :

    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if context['envoimaa'].data_vent:
            # On a des données vent, on va faire en sourte de préparer les données pour le template
            # Rappelle (echeance, (ff,fx,dd)) => données en kt
            # Changement d'unité si besoin 
            data = json.loads(context['envoimaa'].data_vent)
            station = context['envoimaa'].configmaa.station
            # On reconstitue une série avec les formats nécessaires au  template :
            other = []
            for echeance, (ff, fx, dd) in data:
                other.append({  "echeance": datetime.strptime(echeance, "%Y-%m-%d %H:%M:%S"), 
                                "ff": station.get_wind_with_station_unit(ff),
                                "fx": station.get_wind_with_station_unit(fx),
                                "dd": dd
                })
            context["data_vent"] = other

        if context['envoimaa'].data_tempe:
            # On a des données tempé, on va faire en sourte de préparer les données pour le template
            # Rappelle (echeance, t°) => données en °C
            data = json.loads(context['envoimaa'].data_tempe)
            station = context['envoimaa'].configmaa.station
            # On reconstitue une série avec les formats nécessaires au  template :
            echeances = []
            values = []
            for echeance, t in data:
                echeances.append(datetime.strftime( datetime.strptime(echeance, "%Y-%m-%d %H:%M:%S"), "%H"))
                values.append(str(t))
            
            context["echeances"] = ",".join(echeances)
            context["temperatures"] = ",".join(values)
            context["seuil"] = str(context['envoimaa'].configmaa.seuil)
        return context