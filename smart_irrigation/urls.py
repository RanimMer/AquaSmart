from django.contrib import admin 
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from users.views import CustomLoginView, signup
from cultures import views as cultures_views
from produits import views as produits_views
from station_meteo import views as station_views
from sols import views as sols_views
from serre import views as serre_views
from users import views as users_views



urlpatterns = [
    path('admin/', admin.site.urls),

    # FRONT public (pages statiques)
    path('',TemplateView.as_view(template_name='public/index.html',extra_context={'active_page': 'home'}),name='index'),
    path('apropos/', TemplateView.as_view(template_name='public/apropos.html'), name='apropos'),
    path('contact/', TemplateView.as_view(template_name='public/contact.html'), name='contact'),
    path('cultures/', cultures_views.cultures, name='cultures'),
    path('produits/', produits_views.produits, name='produits'),
    path('station_meteo/', station_views.station_meteo, name='station_meteo'),
    path('analyses-sols/', sols_views.liste_sols_front, name='liste_sols_front'),
    path('analyses-sols/<int:id_analyse>/', sols_views.details_sol_front, name='details_sol_front'),
    path('serres/', serre_views.serres, name='serres'),
    path('profil/', users_views.front_profile_view, name='front_profile'),


    # Backoffice + modules
    path('backoffice/', TemplateView.as_view(template_name='backoffice/dashboard.html'), name='bo_dashboard'),
    path('backoffice/', include('users.urls')),
    path('backoffice/', include('produits.urls')),
    path('backoffice/', include('cultures.urls')),
    path('backoffice/', include('sols.urls')),
    path('backoffice/', include('station_meteo.urls')),
    path('serre/', include('serre.urls')),

    # ✅ URLs du module Station Météo (front + back déjà définis dans l'app)
    #path('', include('station_meteo.urls')),
    

    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),

    # Reset MDP
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
