from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('station_meteo/', views.gestion_station_meteo, name='gestion_station_meteo'),
    path('station_meteo/ajouter/', views.StationMeteoCreateView.as_view(), name='ajouter_station_meteo'),
    path('station_meteo/modifier/<str:pk>/', views.StationMeteoUpdateView.as_view(), name='modifier_station_meteo'),
    path('station_meteo/supprimer/<str:pk>/', views.StationMeteoDeleteView.as_view(), name='supprimer_station_meteo'),
]
