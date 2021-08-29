from django.contrib import admin

from myproject.apps.core.models import EnvoiMAA, Profile, Region, Station, ConfigMAA, EnvoiMAA


class ConfMAAInline(admin.TabularInline):
    model = ConfigMAA
    extra = 3

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

class EnvoiMAAAdmin(admin.ModelAdmin):

    list_display = ('numero', 'date_envoi', 'configmaa')
    #search_fields = ['numero']


class ConfigMAAAdmin(admin.ModelAdmin):
    list_display = ('station', 'type_maa', 'seuil', 'auto', 'pause', 'scan', 'profondeur')


# Register your models here.
admin.site.register(Profile)
admin.site.register(Region)
admin.site.register(Station, StationAdmin)
admin.site.register(ConfigMAA, ConfigMAAAdmin)
admin.site.register(EnvoiMAA, EnvoiMAAAdmin)
