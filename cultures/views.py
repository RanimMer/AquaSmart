from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages

from .models import Culture, CultureProduit
from .forms import CultureForm
from produits.models import Produit
from sols.models import AnalyseSol
from users.models import Farm
from django.db.models import Sum
from reportlab.pdfgen import canvas  
from django.http import HttpResponse
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from datetime import date, timedelta
from calendar import monthrange
from django.utils import timezone
import calendar
import json
from cultures.services_notifications import envoyer_notifications_cultures_pour_aujourdhui

from django.core.files.storage import default_storage
from ai_engine.plant_health_inference import predict_plant_health

def dashboard(request):
    nb_fermes = envoyer_notifications_cultures_pour_aujourdhui()
    if nb_fermes > 0:
            messages.success(request, "📩 Emails envoyés aux agriculteurs de votre ferme.")
    return render(request, 'backoffice/dashboard.html')


# =========================
# Helpers liés aux fermes
# =========================
def _current_farm(request):
    """
    Détermine la ferme courante pour rattacher un nouvel objet :
      - TECH  : profile.farm
      - ADMIN : sa ferme si une seule, sinon la première
    """
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    if hasattr(user, "id"):
        farms = Farm.objects.filter(owner=user)
        if farms.count() == 1:
            return farms.first()
        return farms.first()  # si plusieurs, on prend la première

    return None


def _cultures_for_user(user):
    """
    Retourne les cultures accessibles selon le rôle :
      - TECH  : uniquement celles de sa ferme
      - ADMIN : toutes les cultures de ses fermes
    """
   
    
    if not user.is_authenticated:
        return Culture.objects.none()

    profile = getattr(user, "profile", None)

    # TECH : uniquement sa ferme
    if profile and profile.role == "TECH" and profile.farm:
        return Culture.objects.filter(farm=profile.farm)

    # ADMIN : toutes ses fermes
    if profile and profile.role == "ADMIN":
        return Culture.objects.filter(farm__owner=user)

    return Culture.objects.none()

# =========================


def gestion_cultures(request):
    nb_fermes = envoyer_notifications_cultures_pour_aujourdhui()
    if nb_fermes > 0:
            messages.success(request, "📩 Emails envoyés aux agriculteurs de votre ferme.")
    """Liste des cultures + recherche + tri."""
    cultures_qs = _cultures_for_user(request.user)

    # 🔎 recherche par nom
    q = request.GET.get("q", "").strip()
    if q:
        cultures_qs = cultures_qs.filter(nom__icontains=q)

    # ↕ tri
    tri = request.GET.get("tri")
    if tri == "besoin_asc":
        cultures_qs = cultures_qs.order_by("besoin_base_l_j")
    elif tri == "besoin_desc":
        cultures_qs = cultures_qs.order_by("-besoin_base_l_j")
    elif tri == "semis_asc":
        cultures_qs = cultures_qs.order_by("date_semis")
    elif tri == "semis_desc":
        cultures_qs = cultures_qs.order_by("-date_semis")
    else:
        cultures_qs = cultures_qs.order_by("nom")

    return render(
        request,
        "backoffice/gestion_cultures.html",
        {
            "cultures": cultures_qs,
            "q": q,
            "tri": tri,
        },
    )




def ajouter_culture(request):
    user = request.user
    profile = getattr(user, "profile", None)

    # 🔹 ferme courante
    farm = _current_farm(request)

    if request.method == 'POST':
        form = CultureForm(request.POST, request.FILES)
        # 🔹 on restreint le champ sol AVANT validation
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

        if form.is_valid():
            culture = form.save(commit=False)

            # 🔗 rattacher automatiquement à la ferme de l’utilisateur
            if farm is not None:
                culture.farm = farm

            culture.save()
            form.save_m2m()

            return redirect('gestion_cultures')
    else:
        form = CultureForm()
        # 🔹 ici aussi, pour l’affichage initial
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

    return render(request, 'backoffice/form_culture.html', {
        'form': form,
        'action': 'Ajouter',
    })



def modifier_culture(request, pk):
    user = request.user
    qs = _cultures_for_user(user)
    culture = get_object_or_404(qs, pk=pk)

    # 🔹 ferme liée à cette culture
    farm = culture.farm

    if request.method == 'POST':
        form = CultureForm(request.POST, request.FILES, instance=culture)
        # on limite les sols possibles à la ferme de la culture
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

        if form.is_valid():
            # ⚠️ on NE change pas la ferme ici
            form.save()
            return redirect('gestion_cultures')
    else:
        form = CultureForm(instance=culture)
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

    return render(request, 'backoffice/form_culture.html', {
        'form': form,
        'action': 'Modifier',
    })


def supprimer_culture(request, pk):
    user = request.user
    qs = _cultures_for_user(user)
    culture = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        culture.delete()
        return redirect('gestion_cultures')

    return render(request, 'backoffice/gestion_culture.html', {'culture': culture})


@transaction.atomic
def enregistrer_utilisation_produit(request, culture_id):
    user = request.user
    qs = _cultures_for_user(user)
    culture = get_object_or_404(qs, id=culture_id)

    # 🔹 IMPORTANT : on limite aux produits de la même ferme
    produits = Produit.objects.filter(farm=culture.farm)

    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        quantite_utilisee = request.POST.get('quantite_utilisee')

        if not produit_id or not quantite_utilisee:
            messages.error(request, "Veuillez sélectionner un produit et indiquer une quantité.")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        # sécurité supplémentaire : on récupère le produit dans le queryset filtré
        produit = get_object_or_404(produits, id=produit_id)

        try:
            quantite_utilisee = int(float(quantite_utilisee))
        except ValueError:
            messages.error(request, "La quantité doit être un nombre entier valide.")
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        stock_actuel = int(float(produit.quantite_stock.split()[0]))  # "160 sachets" -> 160
        if quantite_utilisee > stock_actuel:
            messages.error(
                request,
                f"Quantité insuffisante en stock ({stock_actuel} disponibles).",
                extra_tags='small-message'
            )
            return redirect('enregistrer_utilisation_produit', culture_id=culture_id)

        CultureProduit.objects.create(
            culture=culture,
            produit=produit,
            quantite_utilisee=quantite_utilisee
        )

        unite = produit.quantite_stock.split(' ', 1)[1]
        nouveau_stock = stock_actuel - quantite_utilisee
        produit.quantite_stock = f"{nouveau_stock} {unite}"
        produit.save()

        messages.success(
            request,
            f"{quantite_utilisee} {unite} de {produit.nom_produit} ont été utilisés pour {culture.nom}."
        )
        return redirect('gestion_cultures')

    return render(request, 'backoffice/utiliser_produit.html', {
        'culture': culture,
        'produits': produits
    })

def cultures(request):
    """
    Page front-office :
      - Liste des cultures (cartes)
      - Barre de recherche / voix (déjà dans le template)
      - + Analyse IA d'une photo de plante (upload image)
    """
    label = None
    confidence = None

    # 🔔 Notifications email (comme avant)
    if request.user.is_authenticated:
        nb_fermes = envoyer_notifications_cultures_pour_aujourdhui()
        if nb_fermes > 0:
            messages.success(request, "📩 Emails envoyés aux agriculteurs de votre ferme.")

        items = _cultures_for_user(request.user)
    else:
        items = Culture.objects.none()

    # 📸 PARTIE IA : analyse d'image de plante
    if request.method == "POST" and request.FILES.get("image"):
        img_file = request.FILES["image"]

        # On sauvegarde l'image dans un dossier temporaire MEDIA/tmp/plant_analysis/
        tmp_path = default_storage.save(f"tmp/plant_analysis/{img_file.name}", img_file)
        full_path = os.path.join(settings.MEDIA_ROOT, tmp_path)

        # 🔮 Appel du modèle IA
        label, confidence = predict_plant_health(full_path)

        

    return render(request, 'public/cultures.html', {
        'cultures': items,
        'active_page': 'cultures',
        'label': label,
        'confidence': confidence,
    })



def stats_cultures(request):
    """
    Statistiques avec répartition par type et détails par culture
    """
    cultures_qs = _cultures_for_user(request.user)

    # 1. Stats par type (pour le bar chart et tableau)
    stats_par_type = (
        cultures_qs
        .values("type")
        .annotate(surface_totale=Sum("surface_m2"))
        .order_by("-surface_totale")
    )

    type_labels = dict(Culture.TYPE_CHOICES)

    labels = [type_labels.get(row["type"], row["type"]) for row in stats_par_type]
    data = [float(row["surface_totale"] or 0) for row in stats_par_type]
    
    total_surface = sum(data) if data else 0
    
    # Préparer les stats avec pourcentages
    stats = []
    for row in stats_par_type:
        surface = float(row["surface_totale"] or 0)
        percentage = (surface / total_surface * 100) if total_surface > 0 else 0
        stats.append({
            "type": row["type"],
            "surface_totale": surface,
            "percentage": round(percentage, 1)
        })

    # 2. Stats détaillées par culture dans chaque type
    stats_detaillees = []
    for type_item in stats:
        type_cultures = (
            cultures_qs
            .filter(type=type_item["type"])
            .values("nom")
            .annotate(
                surface=Sum("surface_m2"),
                nb_cultures=Count("id")
            )
            .order_by("-surface")
        )
        
        cultures_detaillees = []
        for culture in type_cultures:
            surface_culture = float(culture["surface"] or 0)
            percentage_dans_type = (surface_culture / type_item["surface_totale"] * 100) if type_item["surface_totale"] > 0 else 0
            
            cultures_detaillees.append({
                "nom": culture["nom"],
                "surface": surface_culture,
                "percentage_dans_type": round(percentage_dans_type, 1)
            })
        
        stats_detaillees.append({
            "type": type_item["type"],
            "type_display": type_labels.get(type_item["type"], type_item["type"]),
            "cultures": cultures_detaillees
        })

    return render(
        request,
        "backoffice/stats_cultures.html",
        {
            "stats": stats,
            "stats_detaillees": stats_detaillees,
            "labels": labels,
            "data": data,
            "total_surface": total_surface,
            "total_cultures": cultures_qs.count(),
        },
    )

def export_cultures_pdf(request):
    """
    Export PDF avec gestion multi-lignes pour les produits
    """
    cultures_qs = (
        _cultures_for_user(request.user)
        .select_related('sol')
        .prefetch_related('cultureproduit_set__produit')
        .order_by("date_semis", "nom")
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="cultures_rapport.pdf"'

    p = canvas.Canvas(response)
    p.setTitle("Rapport des cultures")

    # Couleurs pour correspondre à l'image
    COLOR_GREEN = (0.0, 0.5, 0.0)  # Vert comme dans l'image
    COLOR_BLUE = (0.0, 0.0, 0.8)   # Bleu pour les titres
    COLOR_GRAY = (0.9, 0.9, 0.9)   # Gris clair pour les lignes alternées

    # Titre principal en vert
    y = 800
    p.setFont("Helvetica-Bold", 16)
    p.setFillColorRGB(*COLOR_GREEN)
    p.drawString(50, y, "# RAPPORT DES CULTURES")
    y -= 30

    # Date de génération
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(50, y, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | {cultures_qs.count()} cultures")
    y -= 40

    # En-têtes du tableau en bleu
    p.setFont("Helvetica-Bold", 9)
    p.setFillColorRGB(*COLOR_BLUE)
    
    headers = ["Nom", "Type", "Surface", "Semis", "Récolte", "Eau L/j", "Type sol", "Produits"]
    positions = [50, 100, 150, 200, 250, 310, 360, 430]
    
    for header, pos in zip(headers, positions):
        p.drawString(pos, y, header)
    
    y -= 20

    # Ligne de séparation
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.line(50, y, 550, y)
    y -= 15

    # Données des cultures
    p.setFont("Helvetica", 8)
    for i, c in enumerate(cultures_qs):
        # Type de sol
        if c.sol:
            type_sol = c.sol.get_pin_surface_display()
        else:
            type_sol = "-"
        
        # Produits utilisés - GESTION MULTI-LIGNES
        produits_utilises = c.cultureproduit_set.all()
        if produits_utilises:
            produits_lignes = []
            for cp in produits_utilises:
                produit_text = f"{cp.produit.nom_produit[:15]}({cp.quantite_utilisee})"
                produits_lignes.append(produit_text)
        else:
            produits_lignes = ["-"]
        
        # Calculer le nombre de lignes nécessaires pour cette culture
        nb_lignes_produits = len(produits_lignes)
        hauteur_ligne = max(15, nb_lignes_produits * 12)  # Au moins 15, plus si plusieurs produits
        
        # Fond alterné pour les lignes (couvrir toute la hauteur nécessaire)
        if i % 2 == 0:
            p.setFillColorRGB(*COLOR_GRAY)
            p.rect(50, y - hauteur_ligne + 10, 500, hauteur_ligne, fill=1, stroke=0)
        
        p.setFillColorRGB(0, 0, 0)  # Texte en noir
        
        # Données fixes (première ligne)
        data_fixe = [
            c.nom[:8],
            c.get_type_display()[:10],
            f"{c.surface_m2} m²",
            c.date_semis.strftime('%d/%m/%y'),
            c.date_recolte_prevue.strftime('%d/%m/%y') if c.date_recolte_prevue else '-',
            str(c.besoin_base_l_j),
            type_sol[:10],
            produits_lignes[0] if produits_lignes else "-"  # Premier produit
        ]
        
        # Dessiner les données fixes
        for text, pos in zip(data_fixe, positions):
            p.drawString(pos, y, str(text))
        
        # Dessiner les produits supplémentaires sur les lignes suivantes
        y_produits = y - 12  # Position pour le produit suivant
        for j in range(1, len(produits_lignes)):
            p.drawString(positions[7], y_produits, produits_lignes[j])
            y_produits -= 12
        
        # Descendre pour la prochaine culture
        y = y_produits - 3
        
        # Vérifier si on doit passer à une nouvelle page
        if y < 100:
            p.showPage()
            y = 800
            p.setFont("Helvetica", 8)

    # Résumé avec style comme dans l'image
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.setFillColorRGB(*COLOR_GREEN)
    p.drawString(50, y, "## Résumé")
    y -= 20
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    
    total_surface = sum(float(c.surface_m2) for c in cultures_qs)
    total_besoin = sum(float(c.besoin_base_l_j) for c in cultures_qs)
    
    p.drawString(50, y, f"Surface totale: {total_surface} m²")
    y -= 15
    p.drawString(50, y, f"Besoin eau total: {total_besoin} L/j")
    y -= 15
    p.drawString(50, y, f"Nombre de cultures: {cultures_qs.count()}")

    p.showPage()
    p.save()
    return response


# Noms des mois en français (pour l'en-tête du calendrier)
MONTH_NAMES_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def estimer_frequence_jours(culture: Culture) -> int:
    """
    Règle simple et temporaire pour estimer la fréquence d'irrigation
    à partir du besoin en eau (litres/jour).
    Plus tard, tu pourras remplacer ça par ton modèle IA.
    """
    besoin = culture.besoin_base_l_j

    # Sécurité : si besoin n'est pas renseigné
    if besoin is None or besoin <= 0:
        return 3  # fréquence par défaut

    if besoin <= 2:
        return 4  # peu d'eau → moins souvent
    elif besoin <= 5:
        return 3  # besoin moyen
    else:
        return 2  # beaucoup d'eau → plus fréquent


def generer_evenements_irrigation(cultures, year: int, month: int):
    """
    Construit un dict pour TOUT le mois demandé:
    {
        "2025-11-10": [
            {"name": ..., "type": ..., "besoin_base_l_j": ..., "frequency_days": ...},
            ...
        ],
        ...
    }
    """
    events_by_date = {}

    # bornes du mois affiché
    first_day_month = date(year, month, 1)
    last_day_month = date(year, month, monthrange(year, month)[1])

    for culture in cultures:
        # S'il manque les dates, on skip
        if not culture.date_semis or not culture.date_recolte_prevue:
            continue

        # Début : pas avant la date de semis, ni avant le début du mois
        start = max(culture.date_semis, first_day_month)

        # Fin : pas après la date de récolte, ni après la fin du mois
        end = min(culture.date_recolte_prevue, last_day_month)

        if start > end:
            # Rien à irriguer dans ce mois-là pour cette culture
            continue

        freq = estimer_frequence_jours(culture)

        # Génère des dates espacées de "freq" jours dans ce mois
        current = start
        while current <= end:
            key = current.isoformat()  # "YYYY-MM-DD"

            if key not in events_by_date:
                events_by_date[key] = []

            events_by_date[key].append({
                "name": culture.nom,
                "type": culture.get_type_display(),
                "besoin_base_l_j": float(culture.besoin_base_l_j or 0),
                "frequency_days": freq,
            })

            current += timedelta(days=freq)

    return events_by_date


def build_weeks(year: int, month: int, events_by_date):
    """
    Construit la structure "weeks" pour le template
    """
    weeks = []

    first_day = date(year, month, 1)
    nb_days = monthrange(year, month)[1]
    last_day = date(year, month, nb_days)

    # On affiche de LUNDI à DIMANCHE
    start = first_day - timedelta(days=first_day.weekday())
    end = last_day + timedelta(days=(6 - last_day.weekday()))

    today = date.today()
    current = start

    while current <= end:
        week = []
        for _ in range(7):
            in_month = (current.month == month)
            key = current.isoformat()
            events_for_day = events_by_date.get(key, [])
            
            # Compter les événements par type
            irrigation_count = 0
            recolte_count = 0
            
            for event in events_for_day:
                if event.get('event_type') == 'recolte':
                    recolte_count += 1
                else:
                    irrigation_count += 1
            
            has_recolte = recolte_count > 0
            has_irrigation = irrigation_count > 0

            # Déterminer le status
            if events_for_day:
                if current < today:
                    status = "past"
                elif current == today:
                    status = "today"
                else:
                    status = "upcoming"
            else:
                status = ""

            week.append({
                "date": current,
                "in_month": in_month,
                "events": events_for_day,  # Changé de "cultures" à "events"
                "status": status,
                "has_recolte": has_recolte,
                "has_irrigation": has_irrigation,
                "irrigation_count": irrigation_count,
                "recolte_count": recolte_count,
            })
            current += timedelta(days=1)

        weeks.append(week)

    return weeks


def calendrier_cultures(request):
    # 1) Récupérer année / mois depuis la query string (ou aujourd’hui par défaut)
    today = date.today()

    try:
        year = int(request.GET.get("year") or today.year)
    except (TypeError, ValueError):
        year = today.year

    try:
        month = int(request.GET.get("month") or today.month)
    except (TypeError, ValueError):
        month = today.month

    # Sécuriser le mois entre 1 et 12
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # 2) Récupérer les cultures visibles par l'utilisateur
    cultures = _cultures_for_user(request.user)

    # 3) Générer les évènements d'irrigation ET de récolte pour ce mois
    events_by_date = generer_evenements_irrigation(cultures, year, month)
    
    # 4) Ajouter les dates de récolte
    add_recolte_dates_to_events(cultures, events_by_date, year, month)

    # 5) Construire la grille (weeks) pour le template
    weeks = build_weeks(year, month, events_by_date)

    # 6) Calculer mois précédent / suivant
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1

    context = {
        "month_name": MONTH_NAMES_FR[month - 1],
        "year": year,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "weeks": weeks,
    }
    return render(request, "public/calendCulture.html", context)


def add_recolte_dates_to_events(cultures, events_by_date, year, month):
    """
    Ajoute les dates de récolte aux événements du calendrier
    """
    for culture in cultures:
        # Vérifier si la culture a une date de récolte
        if hasattr(culture, 'date_recolte_prevue') and culture.date_recolte_prevue:
            recolte_date = culture.date_recolte_prevue
            
            # Vérifier si la date de récolte est dans le mois affiché
            if recolte_date.year == year and recolte_date.month == month:
                date_key = recolte_date.isoformat()
                
                # Créer une copie de la culture avec un type d'événement spécifique
                culture_for_event = {
                    'name': culture.nom,  # CORRECTION: 'nom' au lieu de 'name'
                    'type': culture.type,
                    'besoin_base_l_j': culture.besoin_base_l_j,
                    'frequency_days': getattr(culture, 'frequency_days', 0),  # Vérifier si cet attribut existe
                    'event_type': 'recolte',
                    'date_recolte_prevue': culture.date_recolte_prevue,  # CORRECTION: 'date_recolte_prevue'
                    'culture_obj': culture
                }
                
                # Ajouter à la liste des événements pour cette date
                if date_key in events_by_date:
                    events_by_date[date_key].append(culture_for_event)
                else:
                    events_by_date[date_key] = [culture_for_event]


def index(request):
    """Page d'accueil"""
    return render(request, 'public/index.html')

def apropos(request):
    """Page À propos"""
    return render(request, 'public/apropos.html')

def contact(request):
    """Page Contact"""
    return render(request, 'public/contact.html')




