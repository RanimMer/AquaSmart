from django.urls import path
from . import views 


urlpatterns = [
    path('produits/', views.produits, name='produits'),
    path('cultures/', views.cultures, name='cultures'),
    path('analyses-sol/', views.liste_sols_front, name='liste_sols_front'),
    path('analyses-sol/<int:id_analyse>/', views.details_sol_front, name='details_sol_front'),
    path('logout/', views.logout_view, name='logout'),
    path('apropos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),
    path('', views.index, name='index'),
    path('serres/', views.serres, name='serres'),  # Cette ligne doit être présente
    
]
