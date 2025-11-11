from django.contrib import admin
from .models import Produit,StationMeteo

# Register your models here.
admin.site.register(Produit)

@admin.register(StationMeteo)
class StationMeteoAdmin(admin.ModelAdmin):
    list_display = (
        'id_station', 
        'nom_station', 
        'emplacement', 
        'date_installation', 
        'actif'
    )
    list_filter = ('actif', 'date_installation')
    search_fields = ('id_station', 'nom_station', 'emplacement')
    readonly_fields = ('id_station', 'date_installation')
    
    fieldsets = (
        ('Informations Station', {
            'fields': ('id_station', 'nom_station', 'emplacement', 'actif')
        }),
        ('Identifiants Capteurs', {
            'fields': (
                'id_sol',
                'id_capteur_pluie', 
                'id_capteur_luminosite_humidite',
                'id_capteur_vent'
            ),
            'classes': ('collapse',)
        }),
    )
    # admin.py

