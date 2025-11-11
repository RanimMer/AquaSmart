from django.shortcuts import render
from backoffice.models import Produit , Culture , AnalyseSol , Plantation, StationMeteo

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



def index(request):
    return render(request, 'index.html')

def Plantation(request):
    # liste des cultures pour le front
    items = Plantation.objects.all()
    return render(request, 'Plantation.html', {'Plantation': items})

def logout_view(request):
    return render(request, 'logout.html')

def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')

from backoffice.models import Plantation

def serres(request):
    """Vue front-office pour afficher les serres"""
    plantations = Plantation.objects.all().order_by('-dateDerniereMiseAJour')
    
    # Ajouter la dernière date d'irrigation pour chaque plantation
    for plantation in plantations:
        plantation.derniere_irrigation = ""
        plantation.prochain_arrosage = "À planifier"  # Par défaut
        
        if plantation.datesIrrigation:
            dates_list = plantation.datesIrrigation.strip().split('\n')
            if dates_list:
                plantation.derniere_irrigation = dates_list[-1].strip()
    
    context = {
        'plantations': plantations,
        'active_page': 'serres'
    }
    return render(request, 'serres.html', context)







# Create your views here.
def index(request):
    return render(request, 'index.html')


def station_meteo(request):
    
    stations = StationMeteo.objects.all()  # Récupère toutes les stations depuis la BDD
    return render(request, 'station_meteo.html', {'stations': stations})


def logout_view(request):
    return render(request, 'logout.html')
    
def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')
