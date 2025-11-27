from django.urls import path
from . import views

urlpatterns = [
    path('produits/', views.gestion_produits, name='gestion_produits'),
    path('produits/ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('produits/modifier/<int:pk>/', views.modifier_produit, name='modifier_produit'),
    path('produits/statistiques/', views.statistiques_produits, name='statistiques_produits'),
    path('produits/export-pdf/', views.export_pdf_produits, name='export_pdf_produits'),
    # optionnel, si tu l’utilises dans le template :
    path('produits/verifier-stock/', views.verifier_stock, name='verifier_stock'),
]
