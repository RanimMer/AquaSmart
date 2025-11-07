from django.shortcuts import render, get_object_or_404, redirect
from ..models import Culture
from ..forms import CultureForm
from django.db import transaction
from backoffice.models import Produit
from django.contrib import messages
from ..models import CultureProduit



# Dashboard existant
def dashboard(request):
    return render(request, 'backoffice/dashboard.html')

def gestion_cultures(request):
    cultures = Culture.objects.all()
    return render(request, 'backoffice/gestion_cultures.html', {'cultures': cultures})

def ajouter_culture(request):
    if request.method == 'POST':
        form = CultureForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gestion_cultures')
    else:
        form = CultureForm()
    return render(request, 'backoffice/form_culture.html', {'form': form, 'action': 'Ajouter'})

def modifier_culture(request, pk):
    culture = get_object_or_404(Culture, pk=pk)
    if request.method == 'POST':
        form = CultureForm(request.POST, request.FILES, instance=culture)
        if form.is_valid():
            form.save()
            return redirect('gestion_cultures')
    else:
        form = CultureForm(instance=culture)
    return render(request, 'backoffice/form_culture.html', {'form': form, 'action': 'Modifier'})

def supprimer_culture(request, pk):
    culture = get_object_or_404(Culture, pk=pk)
    if request.method == 'POST':
        culture.delete()
        return redirect('gestion_cultures')
    return render(request, 'backoffice/supprimer_culture.html', {'culture': culture})

@transaction.atomic
def enregistrer_utilisation_produit(request, culture_id):
    """
    Vue pour enregistrer l'utilisation d'un produit dans une culture
    et mettre à jour automatiquement le stock du produit.
    Les quantités sont traitées comme des entiers.
    """
    culture = get_object_or_404(Culture, id=culture_id)
    produits = Produit.objects.all()

    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        quantite_utilisee = request.POST.get('quantite_utilisee')

        # Vérification des champs
        if not produit_id or not quantite_utilisee:
            messages.error(request, "Veuillez sélectionner un produit et indiquer une quantité.")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        produit = get_object_or_404(Produit, id=produit_id)

        try:
            quantite_utilisee = int(float(quantite_utilisee))  # Convertir en entier
        except ValueError:
            messages.error(request, "La quantité doit être un nombre entier valide.")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        # Vérification du stock
        stock_actuel = int(float(produit.quantite_stock.split()[0]))  # "160 sachets" → 160
        if quantite_utilisee > stock_actuel:
            messages.error(request, f"Quantité insuffisante en stock ({stock_actuel} disponibles).")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        # 🔹 Création de l’association dans CultureProduit
        CultureProduit.objects.create(
            culture=culture,
            produit=produit,
            quantite_utilisee=quantite_utilisee
        )

        # 🔹 Mise à jour du stock
        unite = produit.quantite_stock.split(' ', 1)[1]  # Tout ce qui vient après le premier espace
        nouveau_stock = stock_actuel - quantite_utilisee
        produit.quantite_stock = f"{nouveau_stock} {unite}"
        produit.save()

        messages.success(request, f"{quantite_utilisee} {unite} de {produit.nom_produit} ont été utilisés pour {culture.nom}.")
        return redirect('gestion_cultures')

    return render(request, 'backoffice/utiliser_produit.html', {
        'culture': culture,
        'produits': produits
    })

