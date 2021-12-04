from django.shortcuts import render
from django.views.generic import FormView
from django.conf import settings

from configurateur.models import Station
from donneur.commons import retrieveDatasAero, retrieveDatasCDPH_metropole, retrieveDatasCDPQ_metropole
from donneur.commons import retrieveDatasCDPH_om, retrieveDatasCDPQ_om

from .forms import RetrievePastDatasForm

class RetrievePastDatasView(FormView):
    form_class = RetrievePastDatasForm
    template_name = 'donneur/retrieve_past_datas.html'

    """def get(self, request, *args, **kwargs):
        print(request.GET)
        if self.extra_context is None:
            self.extra_context= {}
        self.extra_context['je_valide']="Moi"

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
            
        return self.render_to_response(self.get_context_data())"""

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        if self.extra_context is None:
            self.extra_context= {}
        datas = form.cleaned_data
        
        oaci = datas['station']
        station = Station.objects.get(oaci = oaci) 
        
        self.extra_context['station']= oaci
        self.extra_context['inseepp']= station.inseepp
        self.extra_context['heure_analyse']= datas['heure_analyse']
        
        station_liste = [(station.oaci, station.inseepp)]
        # Récupération des données Aéro :
        data_aero = retrieveDatasAero([(station.oaci, station.inseepp, station.outremer)], settings.REMOTE_CDPAERO_ARCHIVE).get(oaci, ["Données aéro non récupérées."])
        
        if station.outremer:
            data_h = retrieveDatasCDPH_om(station_liste, settings.REMOTE_CDPH_OM_ARCHIVE).get(oaci, ["Données H non récupérées."])
            data_q = retrieveDatasCDPQ_om(station_liste, settings.REMOTE_CDPQ_OM_ARCHIVE).get(oaci, ["Données Q non récupérées."])
        else:
            data_h = retrieveDatasCDPH_metropole(station_liste, settings.REMOTE_CDPH_ARCHIVE).get(oaci, ["Données H non récupérées."])
            data_q = retrieveDatasCDPQ_metropole(station_liste, settings.REMOTE_CDPQ_ARCHIVE).get(oaci, ["Données Q non récupérées."])


        self.extra_context['data_aero']= "\n".join(data_aero)
        self.extra_context['data_h']= "\n".join(data_h)
        self.extra_context['data_q']= "\n".join(data_q)

        return self.render_to_response(self.get_context_data(form=form))
