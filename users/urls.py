from django.urls import path
from . import views

urlpatterns = [
    # UTILISATEURS (backoffice)
    path('utilisateurs/', views.users_list, name='users_list'),
    #path('utilisateurs/create/', views.user_create, name='user_create'),
    path('utilisateurs/<int:pk>/edit/', views.user_edit, name='user_edit'),  # Changé user_id en pk
    path('utilisateurs/<int:user_id>/delete/', views.user_delete, name='user_delete'),

    # FERMES (backoffice)
    path('fermes/', views.farm_list, name='farm_list'),
    path('fermes/create/', views.farm_create, name='farm_create'),
    path('fermes/<int:pk>/edit/', views.farm_update, name='farm_update'),
    path('fermes/<int:pk>/delete/', views.farm_delete, name='farm_delete'),

    # PROFIL (backoffice)
    path('profil/', views.profile_view, name='profile_view'),
    path('profil/edit/', views.profile_edit, name='profile_edit'),  # Correction du nom
]
