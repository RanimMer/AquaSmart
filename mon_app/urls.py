from django.urls import path
from . import views
from mon_app.views import chatbot_ia, chatbot_api

urlpatterns = [
    path('produits/', views.produits, name='produits'),
    path('logout/', views.logout_view, name='logout'),
    path('apropos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),
    path('chatbot/', views.chatbot_ia, name='chatbot_ia'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('', views.index, name='index'),
]
