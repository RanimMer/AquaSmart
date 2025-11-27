from django.contrib import admin
from .models import Culture, CultureProduit

@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type', 'farm')          # ← 'type' au lieu de 'type_culture'
    search_fields = ('nom',)
    list_filter = ('type', 'farm')                   # ← 'type' au lieu de 'type_culture'

@admin.register(CultureProduit)
class CultureProduitAdmin(admin.ModelAdmin):
    list_display = ('culture', 'produit', 'quantite_utilisee')
