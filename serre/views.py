from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Plantation
from .forms import PlantationForm 
from sols.models import AnalyseSol
from users.models import Farm
from datetime import datetime, timedelta
import re

# +++ AJOUT
def _current_farm(request):
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    farms = Farm.objects.filter(owner=user)
    if farms.exists():
        return farms.first()  # même logique que produits/cultures/sols
    return None

# +++ AJOUT
def _plantations_for_user(user):
    profile = getattr(user, "profile", None)
    if profile and profile.role == "TECH" and profile.farm:
        return Plantation.objects.filter(farm=profile.farm)
    elif profile and profile.role == "ADMIN":
        return Plantation.objects.filter(farm__owner=user)
    return Plantation.objects.none()

# +++ NOUVELLE FONCTION : Calcul du prochain arrosage
def _calculer_prochain_arrosage(plantation):
    """Calcule automatiquement la date du prochain arrosage"""
    if not plantation.datesIrrigation:
        return "À planifier"
    
    dates_list = plantation.datesIrrigation.strip().split('\n')
    if not dates_list:
        return "À planifier"
    
    # Récupérer la dernière date d'arrosage
    derniere_date_str = dates_list[-1].strip()
    
    try:
        # Convertir la dernière date en objet date
        derniere_date = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
        aujourdhui = timezone.now().date()
        
        # Analyser la fréquence d'arrosage
        frequence = plantation.frequenceArrosage.lower() if plantation.frequenceArrosage else ""
        
        jours_ajouter = 0
        
        if "tous les jours" in frequence or "quotidien" in frequence:
            jours_ajouter = 1
        elif "tous les 2 jours" in frequence:
            jours_ajouter = 2
        elif "tous les 3 jours" in frequence:
            jours_ajouter = 3
        elif "tous les 4 jours" in frequence:
            jours_ajouter = 4
        elif "tous les 5 jours" in frequence:
            jours_ajouter = 5
        elif "tous les 6 jours" in frequence:
            jours_ajouter = 6
        elif "hebdomadaire" in frequence or "toutes les semaines" in frequence:
            jours_ajouter = 7
        elif "tous les 15 jours" in frequence:
            jours_ajouter = 15
        else:
            # Essayer de trouver un nombre dans la fréquence
            match = re.search(r'(\d+)\s*jour', frequence)
            if match:
                jours_ajouter = int(match.group(1))
            else:
                return "À planifier"
        
        # Calculer la prochaine date
        prochaine_date = derniere_date + timedelta(days=jours_ajouter)
        
        # Vérifier si c'est aujourd'hui ou dans le futur
        if prochaine_date == aujourdhui:
            return "AUJOURD'HUI"
        elif prochaine_date < aujourdhui:
            return "EN RETARD"
        else:
            return prochaine_date.strftime("%d/%m/%Y")
            
    except ValueError:
        return "Date invalide"

# Vue pour la liste des plantations (FRONT OFFICE - accessible à tous)
def plantation_list(request):
    """Afficher toutes les plantations - FRONT OFFICE"""
    plantations = _plantations_for_user(request.user).order_by('-dateDerniereMiseAJour')
    
    # Vérifier pour chaque plantation si elle a été arrosée aujourd'hui
    aujourdhui = timezone.now().strftime("%d/%m/%Y")
    for plantation in plantations:
        plantation.deja_arrose_aujourdhui = False
        if plantation.datesIrrigation:
            dates_list = plantation.datesIrrigation.strip().split('\n')
            if dates_list and dates_list[-1].strip() == aujourdhui:
                plantation.deja_arrose_aujourdhui = True
        
        # +++ AJOUT : Calcul du prochain arrosage
        plantation.prochain_arrosage_calcule = _calculer_prochain_arrosage(plantation)
    
    context = {
        'plantations': plantations,
        'active_page': 'serre',
        'aujourdhui': aujourdhui
    }
    return render(request, 'backoffice/plantation_list.html', context)

# Vues CRUD (BACK OFFICE - nécessite une connexion)
def plantation_create(request):
    """Créer une nouvelle plantation - BACK OFFICE"""
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES)

        farm = _current_farm(request)
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

        if form.is_valid():
            plantation = form.save(commit=False)
            # +++ AJOUT : rattacher automatiquement à la ferme
            plantation.farm = _current_farm(request)
            plantation.save()
            messages.success(request, f"✅ Plantation '{plantation.nomCulture}' ajoutée avec succès!")
            return redirect('plantation_list')
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PlantationForm()
        # +++ AJOUT : limiter le select de sol à la ferme courante
        farm = _current_farm(request)
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)
    
    context = {
        'form': form,
        'title': 'Ajouter une Plantation',
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_form.html', context)

def plantation_update(request, idSerre):
    """Modifier une plantation existante - BACK OFFICE"""
    plantation = get_object_or_404(_plantations_for_user(request.user), idSerre=idSerre)
    
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES, instance=plantation)

        if plantation.farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=plantation.farm)

        if form.is_valid():
            # ⚠️ on ne touche pas à plantation.farm ici
            form.save()
            messages.success(request, f"✅ Plantation '{plantation.nomCulture}' modifiée avec succès!")
            return redirect('plantation_list')
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PlantationForm(instance=plantation)
        # +++ AJOUT
        if plantation.farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=plantation.farm)
    
    context = {
        'form': form,
        'title': f'Modifier {plantation.nomCulture}',
        'plantation': plantation,
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_form.html', context)

def plantation_delete(request, idSerre):
    """Supprimer une plantation - BACK OFFICE"""
    plantation = get_object_or_404(_plantations_for_user(request.user), idSerre=idSerre)
    
    if request.method == 'POST':
        nom_culture = plantation.nomCulture
        plantation.delete()
        messages.success(request, f"✅ Plantation '{nom_culture}' supprimée avec succès!")
        return redirect('plantation_list')
    
    context = {
        'plantation': plantation,
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_confirm_delete.html', context)

# ✅ NOUVELLE FONCTION POUR ARROSAGE AUTOMATIQUE
def confirmer_arrosage(request, idSerre):
    """Bouton pour confirmer l'arrosage d'aujourd'hui - AUTOMATIQUE"""
    plantation = get_object_or_404(_plantations_for_user(request.user), idSerre=idSerre)
    
    # Vérifier si déjà arrosé aujourd'hui
    aujourdhui = timezone.now().strftime("%d/%m/%Y")
    if plantation.datesIrrigation:
        dates_list = plantation.datesIrrigation.strip().split('\n')
        if dates_list and dates_list[-1].strip() == aujourdhui:
            messages.warning(request, f"⚠️ {plantation.nomCulture} a déjà été arrosée aujourd'hui !")
            return redirect('plantation_list')
    
    # Ajouter automatiquement la date d'aujourd'hui
    if plantation.datesIrrigation:
        plantation.datesIrrigation += f"\n{aujourdhui}"
    else:
        plantation.datesIrrigation = aujourdhui
        
    plantation.save()
    
    messages.success(request, f"✅ {plantation.nomCulture} arrosée aujourd'hui ({aujourdhui}) !")
    return redirect('plantation_list')

def serres(request):
    """Vue front-office pour afficher les serres (front)"""

    if request.user.is_authenticated:
        plantations = _plantations_for_user(request.user).order_by('-dateDerniereMiseAJour')
    else:
        plantations = Plantation.objects.none()

    # Ajouter la dernière date d'irrigation pour chaque plantation
    for plantation in plantations:
        plantation.derniere_irrigation = ""
        plantation.prochain_arrosage = _calculer_prochain_arrosage(plantation)  # +++ MODIFICATION ICI

        if plantation.datesIrrigation:
            dates_list = plantation.datesIrrigation.strip().split('\n')
            if dates_list:
                plantation.derniere_irrigation = dates_list[-1].strip()

    context = {
        'plantations': plantations,
        'active_page': 'serres',
    }
    # ⚠️ mets bien ton template dans templates/public/serres.html
    return render(request, 'public/serres.html', context)

def logout_view(request):
    return render(request, 'logout.html')

def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')