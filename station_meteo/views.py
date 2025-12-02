from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import StationMeteo
from sols.models import AnalyseSol
from .forms import StationMeteoForm
from users.models import Farm  # 🔹 import farm


# ===================== #
#   🔹 Helpers FARM     #
# ===================== #
def _current_farm(request):
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    farms = Farm.objects.filter(owner=user)
    if farms.exists():
        return farms.first()
    return None


def _stations_for_user(user):
    profile = getattr(user, "profile", None)
    if profile and profile.role == "TECH" and profile.farm:
        return StationMeteo.objects.filter(farm=profile.farm)
    elif profile and profile.role == "ADMIN":
        return StationMeteo.objects.filter(farm__owner=user)
    return StationMeteo.objects.none()


# ===================== #
#        🔹 VUES        #
# ===================== #

def dashboard(request):
    return render(request, 'backoffice/dashboard.html')


def gestion_station_meteo(request):
    stations = _stations_for_user(request.user)  # 🔹 filtrage par ferme
    return render(request, 'backoffice/gestion_station_meteo.html', {'stations': stations})


# ---------- CREATE ----------
class StationMeteoCreateView(CreateView):
    model = StationMeteo
    form_class = StationMeteoForm
    template_name = 'backoffice/form_station_meteo.html'
    success_url = reverse_lazy('gestion_station_meteo')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        farm = _current_farm(self.request)
        if farm and 'sol' in form.fields:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['title'] = 'Ajouter une Station Météo'
        context['active_page'] = 'station'
        context['action'] = 'Créer'
        context['sols'] = AnalyseSol.objects.filter(farm=_current_farm(self.request))
        return context

    def form_valid(self, form):
        farm = _current_farm(self.request)
        instance = form.save(commit=False)
        instance.farm = farm  # 🔹 assignation automatique
        instance.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


# ---------- UPDATE ----------
class StationMeteoUpdateView(UpdateView):
    model = StationMeteo
    form_class = StationMeteoForm
    template_name = 'backoffice/form_station_meteo.html'
    success_url = reverse_lazy('gestion_station_meteo')

    def get_queryset(self):
        return _stations_for_user(self.request.user)  # 🔹 restreindre à la ferme

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        station = self.get_object()
        if station.farm and 'sol' in form.fields:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=station.farm)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station = self.get_object()
        context['form'] = self.get_form()
        context['title'] = f"Modifier {station.nom_station}"
        context['station'] = station
        context['active_page'] = 'station'
        context['action'] = 'Modifier'
        context['sols'] = AnalyseSol.objects.filter(farm=_current_farm(self.request))
        return context

    def form_valid(self, form):
        station = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


# ---------- DELETE ----------
class StationMeteoDeleteView(DeleteView):
    model = StationMeteo
    template_name = 'backoffice/supprimer_station_meteo.html'
    success_url = reverse_lazy('gestion_station_meteo')

    def get_queryset(self):
        return _stations_for_user(self.request.user)  # 🔹 sécurisation d’accès

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['station'] = self.object
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Station météo supprimée avec succès!')
        return super().delete(request, *args, **kwargs)
    
# ------------------- FRONT -------------------
def station_meteo(request):
    """
    Page front des stations météo (template: station_meteo.html).
    On garde le même nom de vue et la même variable de contexte 'stations'.
    """
    if request.user.is_authenticated:
        stations = _stations_for_user(request.user)
    else:
        stations = StationMeteo.objects.none()  # pas connecté => rien (modifie si tu veux du public)

    return render(request, 'public/station_meteo.html', {
        'stations': stations,
        'active_page': 'meteo',  # <- pour activer le lien dans la navbar
    })

def index(request):
    """Page d'accueil"""
    return render(request, 'public/index.html')

def apropos(request):
    """Page À propos"""
    return render(request, 'public/apropos.html')

def contact(request):
    """Page Contact"""
    return render(request, 'public/contact.html')



