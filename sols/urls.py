from django.urls import path
from . import views

urlpatterns = [
    path('sols/', views.liste_sols_back, name='liste_sols_back'),
    path('sols/ajouter/', views.ajouter_sol_back, name='ajouter_sol_back'),
    path('sols/modifier/<int:id_analyse>/', views.modifier_sol_back, name='modifier_sol_back'),
    path('sols/supprimer/<int:id_analyse>/', views.supprimer_sol_back, name='supprimer_sol_back'),
]
