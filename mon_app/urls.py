from django.urls import path
from . import views 

urlpatterns = [
    # Page d'accueil principale
    path('', views.index, name='index'),
    
    # Pages statiques
    path('apropos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),
    
    # Analyses sol - FRONTOFFICE
    path('analyses-sol/', views.liste_sols_front, name='liste_sols_front'),
    path('analyses-sol/<int:id_analyse>/', views.details_sol_front, name='details_sol_front'),
    
    # Authentification
    path('logout/', views.logout_view, name='logout'),

]