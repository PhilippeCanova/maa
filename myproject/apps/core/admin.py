from django.contrib import admin
from django.contrib.admin.models import LogEntry

from myproject.apps.core.models import EnvoiMAA, Profile, Region, Station, ConfigMAA
from myproject.apps.core.models import Client, MediumFTP, MediumMail, MediumSMS


class ConfMAAInline(admin.TabularInline):
    model = ConfigMAA
    extra = 3

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
        ('Paramètres généraux',               {'fields': ['active', 'oaci', 'nom', 'entete', 'region', 'wind_unit', 'temp_unit']}),
        ('Paramètres MAA',               {'fields': [ 'retention', 'reconduction', 'repousse']}),
        ('Gestion des heures', {'fields': ['date_pivot', 'ouverture', 'ouverture1', 'ouverture2', 'fermeture', 'fermeture1', 'fermeture2', 'fuseau']}),
    ]
    inlines = [ConfMAAInline]
    list_display = ('oaci', 'nom', 'region', 'entete', 'active')
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

class EnvoiMAAAdmin(admin.ModelAdmin):

    list_display = ('numero', 'date_envoi', 'status', 'configmaa')
    #search_fields = ['numero']


class ConfigMAAAdmin(admin.ModelAdmin):
    list_display = ('station', 'type_maa', 'seuil', 'auto', 'pause', 'scan', 'profondeur')


# Register your models here.
admin.site.register(Profile)
admin.site.register(Region)
admin.site.register(Station, StationAdmin)
admin.site.register(ConfigMAA, ConfigMAAAdmin)
admin.site.register(EnvoiMAA, EnvoiMAAAdmin)
admin.site.register(Client, ClientAdmin)

class HistoryAdmin(admin.ModelAdmin):
    list_display = ('object_repr', 'action_flag', 'action_time', 'user')
admin.site.register(LogEntry, HistoryAdmin)
