from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('apropos/', views.apropos, name='apropos'),
    path('serres/', views.serres, name='serres'),  # Cette ligne doit être présente
    path('contact/', views.contact, name='contact'),
    path('logout/', views.logout_view, name='logout'),
]