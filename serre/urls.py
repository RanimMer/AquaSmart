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
    path('calendrier/', views.calendrier_backoffice, name='calendrier_backoffice'),
    path('calendrier/front/', views.calendrier_semaine_front, name='calendrier_semaine_front'),
    path('statistiques/', views.statistiques, name='statistiques'),
    # dans urls.py
    path('statistiques/details/<str:type_stat>/<str:categorie>/', views.statistiques_details, name='statistiques_details'),
    path('notifications/', views.notifications, name='notifications'),
     # Notifications
    path('notifications-front/', views.notifications_front, name='notifications_front'),  # Frontoffice
    path('notifications/supprimer/<str:notification_id>/', views.supprimer_notification, name='supprimer_notification'),
    
]