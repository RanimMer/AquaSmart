from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Plantation
from .forms import PlantationForm

# Vue pour la liste des plantations (FRONT OFFICE - accessible à tous)
def plantation_list(request):
    """Afficher toutes les plantations - FRONT OFFICE"""
    plantations = Plantation.objects.all().order_by('-dateDerniereMiseAJour')
    
    context = {
        'plantations': plantations,
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_list.html', context)

# Vues CRUD (BACK OFFICE - nécessite une connexion)
@login_required
def plantation_create(request):
    """Créer une nouvelle plantation - BACK OFFICE"""
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES)  # ← CORRIGÉ ICI
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
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_form.html', context)

@login_required
def plantation_update(request, idSerre):
    """Modifier une plantation existante - BACK OFFICE"""
    plantation = get_object_or_404(Plantation, idSerre=idSerre)
    
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES, instance=plantation)  # ← CORRIGÉ ICI
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
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_form.html', context)

@login_required
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