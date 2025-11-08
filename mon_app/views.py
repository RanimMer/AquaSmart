# mon_app/views.py
from django.shortcuts import render
from backoffice.models import Plantation

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