from django.contrib import admin

from django.shortcuts import redirect

from .models import ConfigMAA, Station, MediumMail, MediumSMS, MediumFTP, AutorisedMAAs, Client

class ConfigMAAAdmin(admin.ModelAdmin):
    READONLY_FOR_POP = ['pause', 'scan', 'profondeur']

    #change_form_template = 'admin/change_configMAA_template.html'
    list_display = ('station', 'type_maa', 'seuil', 'auto', 'active', 'pause', 'scan', 'profondeur')
    search_fields = ['station__oaci', 'type_maa', 'station__region__tag']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Fait en sorte d'avoir l'unité inscrit dans le label
        # TODO : récupérer la vraie unité
        unite = 'kt'
        if obj:
            unite = obj.station.wind_unit

        choices = form.base_fields['type_maa'].choices
        new_choices = []
        for t, l in choices:
            if 'VENT' in t:
                l = l + " ({})".format(unite)
            new_choices.append( (t, l) )
        form.base_fields['type_maa'].choices = new_choices

        """if not request.user.has_perm('myproject.apps.core.expert_configmaa'):
            for name in self.READONLY_FOR_POP:
                form.base_fields[name].widget.attrs['readonly'] = True"""
        return form
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('myproject.apps.core.expert_configmaa'):
            return self.READONLY_FOR_POP
        else:
            return []

    def response_add(self, request, obj, post_url_continue=None):
        if self.je_refuse_le_save :
            self.je_refuse_le_save = False
            return redirect(request.get_full_path())
        else:
            return redirect('/admin/core/configmaa/')

    def response_change(self, request, obj):
        if self.je_refuse_le_save :
            self.je_refuse_le_save = False
            return redirect(request.get_full_path())
        else:
            return redirect('/admin/core/configmaa/')

    def save_model(self, request, obj, form, change):
        #obj.user = request.user
        data = form.cleaned_data
        self.je_refuse_le_save = False

        # Vérifie s'il n'y a pas déjà un combo identique configuré
        """
        try:
            # Peut être géré avec UniqueConstraint, voir quand est généré le ValidationError pour intercepter
            conf = ConfigMAA.objects.get(type_maa=data['type_maa'], seuil=data['seuil'], station=data['station'])
            if conf and (conf.id != obj.id):
                messages.set_level(request, messages.ERROR)
                messages.error(request, "L'élément que vous essayez de créer existe déjà.")
                self.je_refuse_le_save = True
                return
        except:
            pass
        """

        # Force le mode manuel pour les MAA qui ne supporte par l'automatisation
        if not AutorisedMAAs.is_automatisable(data['type_maa']):
            obj.auto = False        
        
        # Force l'effacement du seuil si le maa est de type occurrence
        if AutorisedMAAs.is_occurrence(data['type_maa']):
            obj.seuil = None        
        

        super().save_model(request, obj, form, change)

    #readonly_fields = ('pause', 'scan', 'profondeur')
    #form = ConfigMAAForm

class ConfMAAInline(admin.TabularInline):
    model = ConfigMAA
    extra = 3

    def get_readonly_fields(self, request, obj):
        fields =  super().get_readonly_fields(request, obj=obj)
        if not request.user.has_perm('myproject.apps.core.expert_configmaa'):
            fields = tuple(list(fields) + ConfigMAAAdmin.READONLY_FOR_POP)

        return fields
    
class MediumEmailInline(admin.TabularInline):
    model = MediumMail
    extra = 1

class MediumSMSInline(admin.TabularInline):
    model = MediumSMS
    extra = 1

class MediumFTPInline(admin.TabularInline):
    model = MediumFTP
    extra = 1

class StationAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Paramètres généraux',               {'fields': ['active', 'oaci', 'nom', 'inseepp', 'entete', 'region', 'outremer', 'wind_unit', 'temp_unit']}),
        ('Paramètres MAA',               {'fields': [ 'retention', 'reconduction', 'repousse']}),
        ('Gestion des heures', {'fields': ['date_pivot', 'ouverture', 'ouverture_ete', 'ouverture_hiver', 'fermeture', 'fermeture_ete', 'fermeture_hiver', 'fuseau']}),
    ]
    # inlines = [ConfMAAInline]   # Finalement, n'apporte pas grand chose et complique la donne
    list_display = ('oaci', 'nom', 'inseepp', 'region', 'entete', 'active')
    search_fields = ['oaci', 'nom', 'region__tag']


    def get_queryset(self, request):
        region = request.user.profile.region
        if region:
            qs = Station.objects.filter(region = region )
        else: 
            qs = Station.objects.all()
        return qs

class ClientAdmin(admin.ModelAdmin):

    """fieldsets = [
        ('Paramètres généraux',               {'fields': ['active', 'oaci', 'nom', 'entete', 'region', 'wind_unit', 'temp_unit']}),
        ('Paramètres MAA',               {'fields': [ 'retention', 'reconduction', 'repousse']}),
        ('Gestion des heures', {'fields': ['date_pivot', 'ouverture', 'ouverture1', 'ouverture2', 'fermeture', 'fermeture1', 'fermeture2', 'fuseau']}),
    ]"""
    inlines = [MediumEmailInline, MediumSMSInline, MediumFTPInline ]
    list_display = ('nom', 'prenom', 'telephone', 'email')
    #search_fields = ['oaci', 'nom', 'region__tag']

    """def get_queryset(self, request):
        region = request.user.profile.region
        if region:
            qs = Station.objects.filter(region = region )
        else: 
            qs = Station.objects.all()
        return qs"""

admin.site.register(Station, StationAdmin)
admin.site.register(ConfigMAA, ConfigMAAAdmin)
admin.site.register(Client, ClientAdmin)