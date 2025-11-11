from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from users import views as user_views
# Auth views (import directly to avoid alias confusion)
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from users.views import CustomLoginView, signup
from users import views as users_views  # for signup only

urlpatterns = [
    path('admin/', admin.site.urls),

    # FRONT public
    path('', TemplateView.as_view(template_name='public/index.html'), name='index'),
    path('apropos/', TemplateView.as_view(template_name='public/apropos.html'), name='apropos'),
    path('contact/', TemplateView.as_view(template_name='public/contact.html'), name='contact'),

    # Backoffice (page d’accueil) + toutes les routes users/farms sous /backoffice/
    path('backoffice/', TemplateView.as_view(template_name='backoffice/dashboard.html'), name='bo_dashboard'),
    path('backoffice/', include('users.urls')),

    # Authentication URLs avec vue personnalisée
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),

    # Reset MDP
    path('password-reset/', PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
