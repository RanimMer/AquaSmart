from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import AnalyseSol  # Import depuis le modèle local

# 🔹 Liste des analyses (backoffice)
def liste_sols_back(request):
    sols = AnalyseSol.objects.all().order_by('-date_analyse')
    return render(request, 'backoffice/liste_sols.html', {'sols': sols})

# 🔹 Ajouter une nouvelle analyse
def ajouter_sol_back(request):
    if request.method == 'POST':
        AnalyseSol.objects.create(
            pin_surface=request.POST['pin_surface'],
            surface=request.POST['surface'],
            total_region=request.POST['total_region'],
            bundles_composition=request.POST['bundles_composition'],
            ph=request.POST['ph'],
            azote=request.POST['azote'],
            phosphore=request.POST['phosphore'],
            potassium=request.POST['potassium'],
            localisation=request.POST['localisation'],
        )
        messages.success(request, "✅ Analyse ajoutée avec succès.")
        return redirect('liste_sols_back')
    return render(request, 'backoffice/ajouter_sol.html')

# 🔹 Modifier une analyse
def modifier_sol_back(request, id_analyse):
    sol = get_object_or_404(AnalyseSol, pk=id_analyse)
    if request.method == 'POST':
        for field in [
            'pin_surface', 'surface', 'total_region', 'bundles_composition', 'ph', 'azote', 'phosphore', 'potassium',
            'localisation'
        ]:
            setattr(sol, field, request.POST.get(field, getattr(sol, field)))
        sol.save()
        messages.success(request, "✅ Analyse mise à jour avec succès.")
        return redirect('liste_sols_back')
    return render(request, 'backoffice/modifier_sol.html', {'sol': sol})

# 🔹 Supprimer une analyse
def supprimer_sol_back(request, id_analyse):
    sol = get_object_or_404(AnalyseSol, pk=id_analyse)
    if request.method == 'POST':
        sol.delete()
        messages.warning(request, "⚠️ Analyse supprimée avec succès.")
        return redirect('liste_sols_back')
    else:
        return render(request, 'backoffice/supprimer_sol.html', {'sol': sol})

# 🔹 Accueil backoffice
def accueil_backoffice(request):
    return render(request, 'backoffice/dashboard.html')