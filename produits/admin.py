from django.contrib import admin
from .models import Produit

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom_produit', 'type_produit', 'quantite_stock', 'farm')
    search_fields = ('nom_produit', 'type_produit')
    list_filter = ('type_produit', 'farm')
