from django.urls import path
from django.shortcuts import redirect
from .views import plantation_list, plantation_create, plantation_update, plantation_delete

urlpatterns = [
    path('', lambda request: redirect('plantation_list')),
    path('plantations/', plantation_list, name='plantation_list'),
    path('plantations/ajouter/', plantation_create, name='plantation_create'),
    path('plantations/modifier/<int:idSerre>/', plantation_update, name='plantation_update'),
    path('plantations/supprimer/<int:idSerre>/', plantation_delete, name='plantation_delete'),
]
