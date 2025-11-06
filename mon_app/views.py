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
    context = {
        'plantations': plantations
    }
    return render(request, 'serres.html', context)