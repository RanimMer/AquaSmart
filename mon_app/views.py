
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from backoffice1.models import AnalyseSol

# Create your views here.
def index(request):
    return render(request, 'index.html')

def logout_view(request):
    return render(request, 'logout.html')
    
def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')



# 🔹 Liste publique des analyses
def liste_sols_front(request):
    sols = AnalyseSol.objects.all().order_by('-date_analyse')
    return render(request, 'liste_sols.html', {'sols': sols})

# 🔹 Détail d'une analyse
def details_sol_front(request, id_analyse):
    sol = get_object_or_404(AnalyseSol, pk=id_analyse)
    return render(request, 'details_sol.html', {'sol': sol})
