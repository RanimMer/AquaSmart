from django.urls import path
from django.shortcuts import redirect
from . import views  # importe les vues du module serre


urlpatterns = [
    path('', lambda request: redirect('plantation_list')),

    # CRUD plantation
    path('plantations/', views.plantation_list, name='plantation_list'),
    path('plantations/ajouter/', views.plantation_create, name='plantation_create'),
    path('plantations/modifier/<int:idSerre>/', views.plantation_update, name='plantation_update'),
    path('plantations/supprimer/<int:idSerre>/', views.plantation_delete, name='plantation_delete'),

    # Arrosage automatique
    path('arrosage/confirmer/<int:idSerre>/', views.confirmer_arrosage, name='confirmer_arrosage'),
]
