from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from ..models import StationMeteo, AnalyseSol
from ..forms import StationMeteoForm





# Vue pour gestion_station_meteo.html
def dashboard(request):
    return render(request, 'backoffice/dashboard.html')

def gestion_station_meteo(request):
    stations = StationMeteo.objects.all()
    return render(request, 'backoffice/gestion_station_meteo.html', {'stations': stations})

# Vue pour form_station_meteo.html (Création)
class StationMeteoCreateView(CreateView):
    model = StationMeteo
    form_class = StationMeteoForm
    template_name = 'backoffice/form_station_meteo.html'
    success_url = reverse_lazy('gestion_station_meteo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()  # formulaire vierge
        context['title'] = 'Ajouter une Station Météo'
        context['active_page'] = 'station'
        context['action'] = 'Créer'
        context['sols'] = AnalyseSol.objects.all()  # 🔹 mêmes données que plantation_create
        return context

    def form_valid(self, form):
        station = form.save()
        messages.success(self.request, f"✅ Station météo '{station.nom_station}' ajoutée avec succès!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Veuillez corriger les erreurs ci-dessous.")
        return super().form_invalid(form)


class StationMeteoUpdateView(UpdateView):
    model = StationMeteo
    form_class = StationMeteoForm
    template_name = 'backoffice/form_station_meteo.html'
    success_url = reverse_lazy('gestion_station_meteo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station = self.get_object()
        context['form'] = self.get_form()  # formulaire pré-rempli
        context['title'] = f"Modifier {station.nom_station}"
        context['station'] = station
        context['active_page'] = 'station'
        context['action'] = 'Modifier'
        context['sols'] = AnalyseSol.objects.all()  # 🔹 mêmes données que plantation_update
        return context

    def form_valid(self, form):
        station = form.save()
        messages.success(self.request, f"✅ Station météo '{station.nom_station}' modifiée avec succès!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Veuillez corriger les erreurs ci-dessous.")
        return super().form_invalid(form)

# Vue pour supprimer_station_meteo.html
class StationMeteoDeleteView(DeleteView):
    model = StationMeteo
    template_name = 'backoffice/supprimer_station_meteo.html'
    success_url = reverse_lazy('gestion_station_meteo')

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Renommer 'object' en 'station' pour correspondre au template
        context['station'] = self.object
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Station météo supprimée avec succès!')
        return super().delete(request, *args, **kwargs)


