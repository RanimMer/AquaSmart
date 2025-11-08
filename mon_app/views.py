from django.shortcuts import render
from backoffice.models import Produit , Culture , AnalyseSol

# Create your views here.
def index(request):
    return render(request, 'index.html')

def produits(request):
    # Récupérer la valeur du type de produit depuis le formulaire GET
    query_type = request.GET.get('type_produit', '')  # '' si rien n'est saisi

    if query_type:
        # Filtrer les produits dont le type contient la valeur saisie (insensible à la casse)
        produits = Produit.objects.filter(type_produit__icontains=query_type)
    else:
        # Sinon, afficher tous les produits
        produits = Produit.objects.all()

    # Envoyer les produits et la valeur de la recherche au template
    context = {
        'produits': produits,
        'query_type': query_type
    }
    return render(request, 'produits.html', context)

def cultures(request):
    # liste des cultures pour le front
    items = Culture.objects.all()
    return render(request, 'cultures.html', {'cultures': items})
def liste_sols_front(request):
    sols = AnalyseSol.objects.all().order_by('-date_analyse')
    return render(request, 'liste_sols.html', {'sols': sols})

# 🔹 Détail d'une analyse
def details_sol_front(request, id_analyse):
    sol = get_object_or_404(AnalyseSol, pk=id_analyse)
    return render(request, 'details_sol.html', {'sol': sol})


def logout_view(request):
    return render(request, 'logout.html')
    
def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')
