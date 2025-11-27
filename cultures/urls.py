from django.urls import path
from . import views

urlpatterns = [
    path('cultures/', views.gestion_cultures, name='gestion_cultures'),
    path('cultures/ajouter/', views.ajouter_culture, name='ajouter_culture'),
    path('cultures/modifier/<int:pk>/', views.modifier_culture, name='modifier_culture'),

    path('cultures/supprimer/<int:pk>/', views.supprimer_culture, name='supprimer_culture'),
    path(
        'cultures/<int:culture_id>/utiliser_produit/',
        views.enregistrer_utilisation_produit,
        name='enregistrer_utilisation_produit'
    ),
    
    
]
