from django.urls import path
from . import views 


urlpatterns = [
    path('produits/', views.produits, name='produits'),
    path('cultures/', views.cultures, name='cultures'),
    path('logout/', views.logout_view, name='logout'),
    path('apropos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),
    path('', views.index, name='index'),
]
