from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # pour le dashboard
    path('produits/', views.gestion_produits, name='gestion_produits'),
    path('produits/ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('produits/modifier/<int:pk>/', views.modifier_produit, name='modifier_produit'),
    path('produits/supprimer/<int:pk>/', views.supprimer_produit, name='supprimer_produit'),
    path('produits/statistiques/', views.statistiques_produits, name='statistiques_produits'),
    path('produits/export-pdf/', views.export_pdf_produits, name='export_pdf_produits'),
    path('produits/', views.gestion_produits, name='produits_list'),
]
