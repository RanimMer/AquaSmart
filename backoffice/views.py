from django.shortcuts import render, get_object_or_404, redirect
from .models import Culture
from .forms import CultureForm

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
