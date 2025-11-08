from django.urls import path
from .views import viewsProduits, viewsCultures, viewsSols


urlpatterns = [
    path('', viewsProduits.dashboard, name='dashboard'),
    path('', viewsCultures.dashboard, name='dashboard'),  
    # Produits
    path('produits/', viewsProduits.gestion_produits, name='gestion_produits'),
    path('produits/ajouter/', viewsProduits.ajouter_produit, name='ajouter_produit'),
    path('produits/modifier/<int:pk>/', viewsProduits.modifier_produit, name='modifier_produit'),
    path('produits/supprimer/<int:pk>/', viewsProduits.supprimer_produit, name='supprimer_produit'),
    path('produits/statistiques/', viewsProduits.statistiques_produits, name='statistiques_produits'),
    path('produits/export-pdf/', viewsProduits.export_pdf_produits, name='export_pdf_produits'),

    # Cultures
    path('cultures/', viewsCultures.gestion_cultures, name='gestion_cultures'),
    path('cultures/ajouter/', viewsCultures.ajouter_culture, name='ajouter_culture'),
    path('cultures/modifier/<int:pk>/', viewsCultures.modifier_culture, name='modifier_culture'),
    path('cultures/supprimer/<int:pk>/', viewsCultures.supprimer_culture, name='supprimer_culture'),
    path('cultures/<int:culture_id>/utiliser_produit/', viewsCultures.enregistrer_utilisation_produit, name='enregistrer_utilisation_produit'),
    #sol
    path('sols/', viewsSols.liste_sols_back, name='liste_sols_back'),
    path('sols/ajouter/', viewsSols.ajouter_sol_back, name='ajouter_sol_back'),
    path('sols/modifier/<int:id_analyse>/', viewsSols.modifier_sol_back, name='modifier_sol_back'),
    path('sols/supprimer/<int:id_analyse>/', viewsSols.supprimer_sol_back, name='supprimer_sol_back'),
]
