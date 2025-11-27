from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages

from .models import Culture, CultureProduit
from .forms import CultureForm
from produits.models import Produit
from sols.models import AnalyseSol
from users.models import Farm


def dashboard(request):
    return render(request, 'backoffice/dashboard.html')


# =========================
# Helpers liés aux fermes
# =========================
def _current_farm(request):
    """
    Détermine la ferme courante pour rattacher un nouvel objet :
      - TECH  : profile.farm
      - ADMIN : sa ferme si une seule, sinon la première
    """
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    if hasattr(user, "id"):
        farms = Farm.objects.filter(owner=user)
        if farms.count() == 1:
            return farms.first()
        return farms.first()  # si plusieurs, on prend la première

    return None


def _cultures_for_user(user):
    """
    Retourne les cultures accessibles selon le rôle :
      - TECH  : uniquement celles de sa ferme
      - ADMIN : toutes les cultures de ses fermes
    """
    if not user.is_authenticated:
        return Culture.objects.none()

    profile = getattr(user, "profile", None)

    # TECH : uniquement sa ferme
    if profile and profile.role == "TECH" and profile.farm:
        return Culture.objects.filter(farm=profile.farm)

    # ADMIN : toutes ses fermes
    if profile and profile.role == "ADMIN":
        return Culture.objects.filter(farm__owner=user)

    return Culture.objects.none()

# =========================


def gestion_cultures(request):
    cultures = _cultures_for_user(request.user)
    return render(request, 'backoffice/gestion_cultures.html', {'cultures': cultures})


def ajouter_culture(request):
    user = request.user
    profile = getattr(user, "profile", None)

    # 🔹 ferme courante
    farm = _current_farm(request)

    if request.method == 'POST':
        form = CultureForm(request.POST, request.FILES)
        # 🔹 on restreint le champ sol AVANT validation
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

        if form.is_valid():
            culture = form.save(commit=False)

            # 🔗 rattacher automatiquement à la ferme de l’utilisateur
            if farm is not None:
                culture.farm = farm

            culture.save()
            form.save_m2m()

            return redirect('gestion_cultures')
    else:
        form = CultureForm()
        # 🔹 ici aussi, pour l’affichage initial
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

    return render(request, 'backoffice/form_culture.html', {
        'form': form,
        'action': 'Ajouter',
    })



def modifier_culture(request, pk):
    user = request.user
    qs = _cultures_for_user(user)
    culture = get_object_or_404(qs, pk=pk)

    # 🔹 ferme liée à cette culture
    farm = culture.farm

    if request.method == 'POST':
        form = CultureForm(request.POST, request.FILES, instance=culture)
        # on limite les sols possibles à la ferme de la culture
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

        if form.is_valid():
            # ⚠️ on NE change pas la ferme ici
            form.save()
            return redirect('gestion_cultures')
    else:
        form = CultureForm(instance=culture)
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

    return render(request, 'backoffice/form_culture.html', {
        'form': form,
        'action': 'Modifier',
    })


def supprimer_culture(request, pk):
    user = request.user
    qs = _cultures_for_user(user)
    culture = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        culture.delete()
        return redirect('gestion_cultures')

    return render(request, 'backoffice/supprimer_culture.html', {'culture': culture})


@transaction.atomic
def enregistrer_utilisation_produit(request, culture_id):
    user = request.user
    qs = _cultures_for_user(user)
    culture = get_object_or_404(qs, id=culture_id)

    # 🔹 IMPORTANT : on limite aux produits de la même ferme
    produits = Produit.objects.filter(farm=culture.farm)

    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        quantite_utilisee = request.POST.get('quantite_utilisee')

        if not produit_id or not quantite_utilisee:
            messages.error(request, "Veuillez sélectionner un produit et indiquer une quantité.")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        # sécurité supplémentaire : on récupère le produit dans le queryset filtré
        produit = get_object_or_404(produits, id=produit_id)

        try:
            quantite_utilisee = int(float(quantite_utilisee))
        except ValueError:
            messages.error(request, "La quantité doit être un nombre entier valide.")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        stock_actuel = int(float(produit.quantite_stock.split()[0]))  # "160 sachets" -> 160
        if quantite_utilisee > stock_actuel:
            messages.error(
                request,
                f"Quantité insuffisante en stock ({stock_actuel} disponibles).",
                extra_tags='small-message'
            )
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        CultureProduit.objects.create(
            culture=culture,
            produit=produit,
            quantite_utilisee=quantite_utilisee
        )

        unite = produit.quantite_stock.split(' ', 1)[1]
        nouveau_stock = stock_actuel - quantite_utilisee
        produit.quantite_stock = f"{nouveau_stock} {unite}"
        produit.save()

        messages.success(
            request,
            f"{quantite_utilisee} {unite} de {produit.nom_produit} ont été utilisés pour {culture.nom}."
        )
        return redirect('gestion_cultures')

    return render(request, 'backoffice/utiliser_produit.html', {
        'culture': culture,
        'produits': produits
    })

def cultures(request):
    if request.user.is_authenticated:
        items = _cultures_for_user(request.user)
    else:
        items = Culture.objects.none()

    return render(request, 'public/cultures.html', {
        'cultures': items,
        'active_page': 'cultures',
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




