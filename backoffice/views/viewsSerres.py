from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from ..models import Plantation
from ..forms import PlantationForm
from backoffice.models import AnalyseSol

# Vue pour la liste des plantations (FRONT OFFICE - accessible à tous)
def plantation_list(request):
    """Afficher toutes les plantations - FRONT OFFICE"""
    plantations = Plantation.objects.all().order_by('-dateDerniereMiseAJour')
    
    # Vérifier pour chaque plantation si elle a été arrosée aujourd'hui
    aujourdhui = timezone.now().strftime("%d/%m/%Y")
    for plantation in plantations:
        plantation.deja_arrose_aujourdhui = False
        if plantation.datesIrrigation:
            dates_list = plantation.datesIrrigation.strip().split('\n')
            if dates_list and dates_list[-1].strip() == aujourdhui:
                plantation.deja_arrose_aujourdhui = True
    
    context = {
        'plantations': plantations,
        'active_page': 'serre',
        'aujourdhui': aujourdhui
    }
    return render(request, 'backoffice/plantation_list.html', context)

# Vues CRUD (BACK OFFICE - nécessite une connexion)
def plantation_create(request):
    sols = AnalyseSol.objects.all()  
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES)
        if form.is_valid():
            plantation = form.save()
            messages.success(request, f"✅ Plantation '{plantation.nomCulture}' ajoutée avec succès!")
            return redirect('plantation_list')
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PlantationForm()
    
    context = {
        'form': form,
        'title': 'Ajouter une Plantation',
        'active_page': 'serre',
        'sols': sols   # ← AJOUT ICI
    }
    return render(request, 'backoffice/plantation_form.html', context)

def plantation_update(request, idSerre):
    plantation = get_object_or_404(Plantation, idSerre=idSerre)
    sols = AnalyseSol.objects.all()  # ← AJOUT ICI
    
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES, instance=plantation)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Plantation '{plantation.nomCulture}' modifiée avec succès!")
            return redirect('plantation_list')
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PlantationForm(instance=plantation)
    
    context = {
        'form': form,
        'title': f'Modifier {plantation.nomCulture}',
        'plantation': plantation,
        'active_page': 'serre',
        'sols': sols   # ← AJOUT ICI
    }
    return render(request, 'backoffice/plantation_form.html', context)

def plantation_delete(request, idSerre):
    """Supprimer une plantation - BACK OFFICE"""
    plantation = get_object_or_404(Plantation, idSerre=idSerre)
    
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
    plantation = get_object_or_404(Plantation, idSerre=idSerre)
    
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