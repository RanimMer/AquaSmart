from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models

from .models import AnalyseSol
from users.models import Farm


# =========================
# Helpers liés aux fermes
# =========================
def _current_farm(request):
    """
    Détermine la ferme courante pour rattacher un nouvel objet :
      - TECH  : profile.farm
      - ADMIN : l'une de ses fermes (si plusieurs, on prend la première)
    """
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    farms = Farm.objects.filter(owner=user)
    if farms.exists():
        # si plusieurs, on prend la première par cohérence avec produits/cultures
        return farms.first()

    return None


def _sols_for_user(user):
    """
    Retourne les analyses accessibles selon le rôle :
      - TECH  : seulement celles de sa ferme
      - ADMIN : toutes celles de ses fermes
    """
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return AnalyseSol.objects.filter(farm=profile.farm)
    elif profile and profile.role == "ADMIN":
        return AnalyseSol.objects.filter(farm__owner=user)
    return AnalyseSol.objects.none()
# =========================


# Dans votre views.py
def liste_sols_back(request):
    sols = AnalyseSol.objects.all()
    
    # Récupérer les régions uniques pour le filtre
    regions_uniques = AnalyseSol.objects.values_list('total_region', flat=True).distinct()
    
    # Filtre par qualité
    qualite = request.GET.get('qualite')
    if qualite:
        sols = sols.filter(qualite_sol=qualite)
    
    # Filtre par niveau de pH
    niveau_ph = request.GET.get('niveau_ph')
    if niveau_ph == 'acide':
        sols = sols.filter(ph__lt=6.0)
    elif niveau_ph == 'optimal':
        sols = sols.filter(ph__range=(6.0, 7.5))
    elif niveau_ph == 'alcalin':
        sols = sols.filter(ph__gt=7.5)
    
    # Filtre par azote
    azote = request.GET.get('azote')
    if azote == 'faible':
        sols = sols.filter(azote__lt=20)
    elif azote == 'moyen':
        sols = sols.filter(azote__range=(20, 40))
    elif azote == 'eleve':
        sols = sols.filter(azote__gt=40)
    
    # Filtre par région
    region = request.GET.get('region')
    if region:
        sols = sols.filter(total_region=region)
    
    # Filtre par plage de surface
    plage_surface = request.GET.get('plage_surface')
    if plage_surface == 'petite':
        sols = sols.filter(surface__lt=5)
    elif plage_surface == 'moyenne':
        sols = sols.filter(surface__range=(5, 20))
    elif plage_surface == 'grande':
        sols = sols.filter(surface__gt=20)
    
    # Tri principal
    tri_principal = request.GET.get('tri_principal')
    if tri_principal == 'date_recent':
        sols = sols.order_by('-date_analyse')
    elif tri_principal == 'date_ancien':
        sols = sols.order_by('date_analyse')
    elif tri_principal == 'surface_croissant':
        sols = sols.order_by('surface')
    elif tri_principal == 'surface_decroissant':
        sols = sols.order_by('-surface')
    elif tri_principal == 'ph_croissant':
        sols = sols.order_by('ph')
    elif tri_principal == 'ph_decroissant':
        sols = sols.order_by('-ph')
    else:
        # Tri par défaut
        sols = sols.order_by('-date_analyse')
    
    # Ordre général
    ordre = request.GET.get('ordre')
    if ordre == 'asc':
        sols = sols.reverse()
    

    context = {
        "sols": sols,
        "regions_uniques": regions_uniques,
     
    }
    
    
    return render(request, 'backoffice/liste_sols.html', {'sols': sols})


def ajouter_sol_back(request):
    user = request.user
    profile = getattr(user, "profile", None)

    if request.method == 'POST':
        # 🔗 rattacher automatiquement à la ferme courante
        farm = _current_farm(request)

        ph = float(request.POST.get('ph'))
        surface = float(request.POST.get('surface'))
        azote = float(request.POST.get('azote'))
        phosphore = float(request.POST.get('phosphore'))
        potassium = float(request.POST.get('potassium'))

        # ✔️ Création et stockage de l'analyse
        analyse = AnalyseSol.objects.create(
            farm=farm,
            pin_surface=request.POST['pin_surface'],
            surface=surface,
            total_region=request.POST['total_region'],
            bundles_composition=request.POST['bundles_composition'],
            ph=ph,
            azote=azote,
            phosphore=phosphore,
            potassium=potassium,
            localisation=request.POST['localisation'],
        )

        # ✔️ Vérification critique
        if analyse.est_critique():
            messages.error(
                request,
                "⚠️ Cette analyse contient des valeurs dangereuses ! Une intervention urgente est recommandée."
            )
        else:
            messages.success(request, "✅ Analyse ajoutée avec succès.")

        return redirect('liste_sols_back')

    return render(request, 'backoffice/ajouter_sol.html')


def modifier_sol_back(request, id_analyse):
    user = request.user

    # Récupérer uniquement les analyses accessibles pour l'utilisateur
    sol = get_object_or_404(AnalyseSol, id_analyse=id_analyse)


    if request.method == 'POST':
        # Champs qui doivent être traités comme des nombres
        numeric_fields = ['ph', 'azote', 'phosphore', 'potassium', 'surface']

        # Tous les champs modifiables
        editable_fields = [
            'pin_surface', 'surface', 'total_region', 'bundles_composition',
            'ph', 'azote', 'phosphore', 'potassium', 'localisation'
        ]

        for field in editable_fields:
            # Récupérer la valeur du formulaire ou garder l'ancienne
            value = request.POST.get(field, getattr(sol, field))

            # Convertir en float si nécessaire
            if field in numeric_fields:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = getattr(sol, field)  # garde l'ancienne valeur si erreur

            setattr(sol, field, value)  # Mettre à jour le champ

        sol.save()
        if sol.est_critique():
           messages.error(
         request,
        "⚠️ Valeurs anormales détectées dans cette analyse !"
    )
        else:
           messages.success(request, "✅ Analyse mise à jour avec succès.")
           return redirect('liste_sols_back')

    return render(request, 'backoffice/modifier_sol.html', {'sol': sol})


def supprimer_sol_back(request, id_analyse):
    user = request.user

   
    sol = get_object_or_404(AnalyseSol, id_analyse=id_analyse)

    if request.method == 'POST':
        sol.delete()
        messages.warning(request, "⚠️ Analyse supprimée avec succès.")
        return redirect('liste_sols_back')

    return render(request, 'backoffice/supprimer_sol.html', {'sol': sol})


def accueil_backoffice(request):
    return render(request, 'backoffice/dashboard.html')

from django.shortcuts import render, get_object_or_404
from .models import AnalyseSol


def liste_sols_front(request):
    """
    Page front qui liste les analyses de sol (FILTRÉ PAR FERME).
    """
    
    if request.user.is_authenticated:
        sols = _sols_for_user(request.user).order_by('-date_analyse')
    else:
        sols = AnalyseSol.objects.none()

    # 🚨 détecter les analyses critiques
    alertes = []
    for sol in sols:
        if sol.est_critique():
            alertes.append({
                "sol": sol,
                "messages": sol.anomalies()
            })

    return render(request, 'public/liste_sols.html', {
        'sols': sols,
        'alertes': alertes,
        'active_page': 'sols',
    })


def details_sol_front(request, id_analyse):
    """
    Page front détail d'une analyse de sol (FILTRÉ PAR FERME).
    """
    qs = _sols_for_user(request.user)

    sol = get_object_or_404(qs, id_analyse=id_analyse)

    return render(request, 'public/details_sol.html', {
        'sol': sol,
        'active_page': 'sols',
    })
import matplotlib
matplotlib.use('Agg')  # Important pour Django
import matplotlib.pyplot as plt
import numpy as np
import io
import urllib, base64
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Min, Max, StdDev
from django.db.models.functions import TruncMonth, TruncWeek

# =========================
# STATISTIQUES ET GRAPHIQUES
# =========================

def statistiques_sols(request):
    """Page principale des statistiques"""
    user = request.user
    sols = _sols_for_user(user)
    
    # Statistiques de base
    stats = {
        'total_analyses': sols.count(),
        'moyenne_ph': sols.aggregate(Avg('ph'))['ph__avg'],
        'moyenne_azote': sols.aggregate(Avg('azote'))['azote__avg'],
        'qualite_distribution': sols.values('qualite_sol').annotate(count=Count('id_analyse')),
        'meilleur_ph': sols.aggregate(Max('ph'))['ph__max'],
        'pire_ph': sols.aggregate(Min('ph'))['ph__min'],
    }
    
    # Génération des graphiques
    graph_qualite = _generer_graphique_qualite(sols)
    graph_evolution = _generer_graphique_evolution(sols)
    graph_correlation = _generer_graphique_correlation(sols)
    graph_repartition_ph = _generer_graphique_repartition_ph(sols)
    
    context = {
        'stats': stats,
        'graph_qualite': graph_qualite,
        'graph_evolution': graph_evolution,
        'graph_correlation': graph_correlation,
        'graph_repartition_ph': graph_repartition_ph,
        'sols': sols.order_by('-date_analyse')[:10],  # Dernières analyses
    }
    
    return render(request, 'backoffice/statistiques_sols.html', context)

def _generer_graphique_qualite(sols):
    """Génère le graphique de distribution de la qualité des sols"""
    try:
        # Données pour le graphique
        qualites = sols.values('qualite_sol').annotate(count=Count('id_analyse'))
        
        if not qualites:
            return None
            
        labels = [q['qualite_sol'].title() for q in qualites]
        counts = [q['count'] for q in qualites]
        
        # Couleurs selon la qualité
        colors = {
            'excellente': '#27ae60',
            'bonne': '#2ecc71', 
            'moyenne': '#f39c12',
            'mauvaise': '#e74c3c',
            'critique': '#c0392b'
        }
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, counts, color=[colors.get(label.lower(), '#3498db') for label in labels])
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.title('Distribution de la Qualité des Sols', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Qualité du Sol', fontsize=12)
        plt.ylabel('Nombre d\'Analyses', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        print(f"Erreur génération graphique qualité: {e}")
        return None

def _generer_graphique_evolution(sols):
    """Génère le graphique d'évolution temporelle du pH"""
    try:
        # Agrégation par mois
        evolution = sols.annotate(
            mois=TruncMonth('date_analyse')
        ).values('mois').annotate(
            ph_moyen=Avg('ph'),
            count=Count('id_analyse')
        ).order_by('mois')
        
        if len(evolution) < 2:
            return None
            
        dates = [e['mois'].strftime('%b %Y') for e in evolution]
        ph_values = [float(e['ph_moyen']) for e in evolution]
        
        plt.figure(figsize=(12, 6))
        
        # Ligne principale
        plt.plot(dates, ph_values, marker='o', linewidth=2.5, markersize=8, 
                color='#9ACD32', label='pH Moyen')
        
        # Zones optimales
        plt.axhline(y=7.5, color='#e74c3c', linestyle='--', alpha=0.7, label='Limite alcaline')
        plt.axhline(y=6.0, color='#3498db', linestyle='--', alpha=0.7, label='Limite acide')
        plt.fill_between(dates, 6.0, 7.5, alpha=0.1, color='#27ae60', label='Zone optimale')
        
        plt.title('Évolution du pH Moyen au Cours du Temps', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Mois', fontsize=12)
        plt.ylabel('pH Moyen', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        print(f"Erreur génération graphique évolution: {e}")
        return None

def _generer_graphique_correlation(sols):
    """Génère un graphique de corrélation entre pH et azote"""
    try:
        # Récupérer les données
        analyses = sols.values('ph', 'azote', 'qualite_sol').filter(ph__isnull=False, azote__isnull=False)
        
        if len(analyses) < 3:
            return None
            
        ph_values = [float(a['ph']) for a in analyses]
        azote_values = [float(a['azote']) for a in analyses]
        qualites = [a['qualite_sol'] for a in analyses]
        
        # Couleurs selon la qualité
        color_map = {
            'excellente': '#27ae60',
            'bonne': '#2ecc71',
            'moyenne': '#f39c12', 
            'mauvaise': '#e74c3c',
            'critique': '#c0392b'
        }
        colors = [color_map.get(q, '#3498db') for q in qualites]
        
        plt.figure(figsize=(10, 8))
        
        # Nuage de points
        scatter = plt.scatter(ph_values, azote_values, c=colors, alpha=0.7, s=60, edgecolors='white', linewidth=0.5)
        
        # Ajouter la régression linéaire
        if len(ph_values) > 1:
            z = np.polyfit(ph_values, azote_values, 1)
            p = np.poly1d(z)
            plt.plot(ph_values, p(ph_values), "r--", alpha=0.8, linewidth=1.5, label='Tendance')
        
        plt.title('Corrélation entre le pH et l\'Azote', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('pH', fontsize=12)
        plt.ylabel('Azote (mg/kg)', fontsize=12)
        
        # Légende personnalisée pour les qualités
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color_map[q], label=q.title()) 
                          for q in set(qualites)]
        plt.legend(handles=legend_elements, title='Qualité du Sol')
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        print(f"Erreur génération graphique corrélation: {e}")
        return None

def _generer_graphique_repartition_ph(sols):
    """Génère un histogramme de la répartition du pH"""
    try:
        ph_values = list(sols.values_list('ph', flat=True).filter(ph__isnull=False))
        
        if not ph_values:
            return None
            
        plt.figure(figsize=(10, 6))
        
        # Histogramme
        n, bins, patches = plt.hist(ph_values, bins=15, alpha=0.7, color='#9ACD32', edgecolor='white')
        
        # Colorier les zones selon le pH
        for i in range(len(patches)):
            if bins[i] < 6.0:
                patches[i].set_facecolor('#e74c3c')  # Acide - rouge
            elif bins[i] > 7.5:
                patches[i].set_facecolor('#3498db')  # Alcalin - bleu
            else:
                patches[i].set_facecolor('#27ae60')  # Optimal - vert
        
        plt.axvline(x=6.0, color='red', linestyle='--', alpha=0.7, label='pH 6.0')
        plt.axvline(x=7.5, color='blue', linestyle='--', alpha=0.7, label='pH 7.5')
        
        plt.title('Répartition des Valeurs de pH', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Valeur de pH', fontsize=12)
        plt.ylabel('Nombre d\'Analyses', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        print(f"Erreur génération graphique répartition pH: {e}")
        return None

def export_statistiques_pdf(request):
    """Export des statistiques en PDF"""
    # Vous pouvez utiliser ReportLab ou WeasyPrint pour générer un PDF
    # Cette fonction nécessite une installation supplémentaire
    pass

