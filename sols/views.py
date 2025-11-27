from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import AnalyseSol
from users.models import Farm


# =========================
# Helpers liés aux fermes
# =========================
def _current_farm(request):
    """
    Détermine la ferme courante pour rattacher un nouvel objet :
      - TECH  : profile.farm
      - ADMIN : l'une de ses fermes (si plusieurs, on prend la première)
    """
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    farms = Farm.objects.filter(owner=user)
    if farms.exists():
        # si plusieurs, on prend la première par cohérence avec produits/cultures
        return farms.first()

    return None


def _sols_for_user(user):
    """
    Retourne les analyses accessibles selon le rôle :
      - TECH  : seulement celles de sa ferme
      - ADMIN : toutes celles de ses fermes
    """
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return AnalyseSol.objects.filter(farm=profile.farm)
    elif profile and profile.role == "ADMIN":
        return AnalyseSol.objects.filter(farm__owner=user)
    return AnalyseSol.objects.none()
# =========================


def liste_sols_back(request):
    sols = _sols_for_user(request.user)
    return render(request, 'backoffice/liste_sols.html', {'sols': sols})


def ajouter_sol_back(request):
    user = request.user
    profile = getattr(user, "profile", None)

    if request.method == 'POST':
        # 🔗 rattacher automatiquement à la ferme courante
        farm = _current_farm(request)

        AnalyseSol.objects.create(
            farm=farm,
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


def modifier_sol_back(request, id_analyse):
    user = request.user

    qs = _sols_for_user(user)
    sol = get_object_or_404(qs,id_analyse=id_analyse)

    if request.method == 'POST':
        for field in [
            'pin_surface', 'surface', 'total_region', 'bundles_composition',
            'ph', 'azote', 'phosphore', 'potassium', 'localisation'
        ]:
            setattr(sol, field, request.POST.get(field, getattr(sol, field)))
        sol.save()
        messages.success(request, "✅ Analyse mise à jour avec succès.")
        return redirect('liste_sols_back')

    return render(request, 'backoffice/modifier_sol.html', {'sol': sol})


def supprimer_sol_back(request, id_analyse):
    user = request.user

    qs = _sols_for_user(user)
    sol = get_object_or_404(qs, id_analyse=id_analyse)

    if request.method == 'POST':
        sol.delete()
        messages.warning(request, "⚠️ Analyse supprimée avec succès.")
        return redirect('liste_sols_back')

    return render(request, 'backoffice/supprimer_sol.html', {'sol': sol})


def accueil_backoffice(request):
    return render(request, 'backoffice/dashboard.html')

from django.shortcuts import render, get_object_or_404
from .models import AnalyseSol


def liste_sols_front(request):
    """
    Page front qui liste les analyses de sol (FILTRÉ PAR FERME).
    """
    if request.user.is_authenticated:
        sols = _sols_for_user(request.user).order_by('-date_analyse')
    else:
        sols = AnalyseSol.objects.none()

    return render(request, 'public/liste_sols.html', {
        'sols': sols,
        'active_page': 'sols',
    })


def details_sol_front(request, id_analyse):
    """
    Page front détail d'une analyse de sol (FILTRÉ PAR FERME).
    """
    qs = _sols_for_user(request.user)

    sol = get_object_or_404(qs, id_analyse=id_analyse)

    return render(request, 'public/details_sol.html', {
        'sol': sol,
        'active_page': 'sols',
    })


