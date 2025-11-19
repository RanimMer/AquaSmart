from django.shortcuts import render, get_object_or_404, redirect
from .models import Produit
from .forms import ProduitForm

# Dashboard existant
def dashboard(request):
    return render(request, 'backoffice/dashboard.html')


# Gestion Produits : affichage liste
def gestion_produits(request):
    produits = Produit.objects.all()
    return render(request, 'backoffice/gestion_produits.html', {'produits': produits})

# Ajouter un produit
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gestion_produits')
    else:
        form = ProduitForm()
    return render(request, 'backoffice/form_produit.html', {'form': form, 'action': 'Ajouter'})

# Modifier un produit
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            return redirect('gestion_produits')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'backoffice/form_produit.html', {'form': form, 'action': 'Modifier'})

# Supprimer un produit
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        return redirect('gestion_produits')
    return render(request, 'backoffice/supprimer_produit.html', {'produit': produit})
