from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # pour le dashboard
    path('cultures/', views.gestion_cultures, name='gestion_cultures'),
    path('cultures/ajouter/', views.ajouter_culture, name='ajouter_culture'),
    path('cultures/modifier/<int:pk>/', views.modifier_culture, name='modifier_culture'),
    path('cultures/supprimer/<int:pk>/', views.supprimer_culture, name='supprimer_culture'),
]

