from django.contrib import admin
from .models import Plantation

@admin.register(Plantation)
class PlantationAdmin(admin.ModelAdmin):
    list_display = (
        'idSerre', 'nomSerre', 'nomCulture', 'variete', 'nombrePlantes',
        'etat', 'dateSemis', 'dateRecoltePrevue', 'datesIrrigation', 'frequenceArrosage'
    )
    search_fields = ('nomSerre', 'nomCulture', 'variete', 'etat')
    list_filter = ('etat', 'frequenceArrosage', 'dateSemis', 'dateRecoltePrevue')
