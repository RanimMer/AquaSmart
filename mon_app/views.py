# mon_app/views.py
from django.shortcuts import render
from backoffice.models import Culture

def index(request):
    return render(request, 'index.html')

def cultures(request):
    # liste des cultures pour le front
    items = Culture.objects.all()
    return render(request, 'cultures.html', {'cultures': items})

def logout_view(request):
    return render(request, 'logout.html')

def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')
