from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# imports graphiques/PDF laissés comme dans ton projet (commentés)
# import matplotlib.pyplot as plt
from io import BytesIO
import base64
import re

# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4, landscape
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Produit
from .forms import ProduitForm
from users.models import Farm


def dashboard(request):
    return render(request, 'backoffice/dashboard.html')


# =========================
# Helpers liés aux fermes
# =========================
def _current_farm(request):
    """
    Détermine la ferme courante pour rattacher un nouvel objet :
      - TECH  : profile.farm (s'il existe)
      - ADMIN : si une seule ferme -> cette ferme, sinon la première
    """
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    if hasattr(user, "id"):
        farms = Farm.objects.filter(owner=user)
        if farms.count() == 1:
            return farms.first()
        return farms.first()  # si plusieurs, on prend la première par défaut

    return None


def _produits_for_user(user):
    """
    Retourne le queryset des produits visibles par l'utilisateur.
      - TECH  : uniquement la ferme du technicien
      - ADMIN : toutes ses fermes
    """
    if not user.is_authenticated:
        return Produit.objects.none()

    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return Produit.objects.filter(farm=profile.farm)

    if profile and profile.role == "ADMIN":
        return Produit.objects.filter(farm__owner=user)

    return Produit.objects.none()

# =========================


def gestion_produits(request):
    sort = request.GET.get('sort', '')
    query = request.GET.get('query', '').strip()

    produits = _produits_for_user(request.user)  # ✅ CORRIGÉ

    # Recherche
    if query:
        produits = produits.filter(
            Q(nom_produit__icontains=query) |
            Q(type_produit__icontains=query) |
            Q(description__icontains=query)
        )

    # Tri Python sur quantite_stock
    def extract_number(quantite):
        match = re.search(r'\d+(\.\d+)?', str(quantite))
        return float(match.group()) if match else 0

    produits = list(produits)
    if sort == 'asc':
        produits.sort(key=lambda p: extract_number(p.quantite_stock))
    elif sort == 'desc':
        produits.sort(key=lambda p: extract_number(p.quantite_stock), reverse=True)

    # Seuils et notifications (logique d'origine)
    seuils = {
        'Graines': 50,
        'Médicaments': 50,
        'Matériel agricole': 5,
        'Légumes': 30,
        'Fruits': 30,
    }

    for p in produits:
        seuil = seuils.get(p.type_produit)
        if seuil is not None:
            quantite = extract_number(p.quantite_stock)
            if quantite < seuil:
                messages.warning(
                    request,
                    f"Quantité insuffisante : {p.nom_produit} ({p.type_produit}) → {quantite} < {seuil}"
                )

    return render(request, 'backoffice/gestion_produits.html', {
        'produits': produits,
        'query': query,
        'sort': sort
    })


def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save(commit=False)

            # 🔗 rattacher automatiquement à la ferme
            farm = _current_farm(request)
            if farm is not None:
                produit.farm = farm

            produit.save()
            return redirect('gestion_produits')
    else:
        form = ProduitForm()

    return render(request, 'backoffice/form_produit.html', {'form': form, 'action': 'Ajouter'})


def modifier_produit(request, pk):
    produits = _produits_for_user(request.user)  # ✅ CORRIGÉ
    produit = get_object_or_404(produits, pk=pk)

    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            # on ne touche pas à produit.farm ici
            form.save()
            return redirect('gestion_produits')
    else:
        form = ProduitForm(instance=produit)

    return render(request, 'backoffice/form_produit.html', {'form': form, 'action': 'Modifier'})


def supprimer_produit(request, pk):
    produits = _produits_for_user(request.user)  # ✅ CORRIGÉ
    produit = get_object_or_404(produits, pk=pk)

    if request.method == 'POST':
        produit.delete()
        return redirect('gestion_produits')

    return render(request, 'backoffice/supprimer_produit.html', {'produit': produit})


def statistiques_produits(request):
    produits = _produits_for_user(request.user)  # ✅ CORRIGÉ
    stats = produits.values('type_produit').annotate(total=Count('id'))

    labels = [item['type_produit'] for item in stats]
    values = [item['total'] for item in stats]

    # si matplotlib est commenté, n'appelle pas cette vue (le lien doit rester commenté).
    fig, ax = plt.subplots()  # type: ignore[name-defined]
    ax.pie(values, labels=labels, autopct='%1.1f%%')
    buffer = BytesIO()
    plt.savefig(buffer, format='png')  # type: ignore[name-defined]
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graph = base64.b64encode(image_png).decode('utf-8')
    return render(request, 'backoffice/statistiques_produits.html', {'graph': graph})


def export_pdf_produits(request):
    produits = _produits_for_user(request.user)  # ✅ CORRIGÉ

    # idem : si reportlab est commenté, ne pas appeler cette vue (lien commenté).
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="liste_produits.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))  # type: ignore[name-defined]
    elements = []
    styles = getSampleStyleSheet()  # type: ignore[name-defined]

    title = Paragraph("<b>Liste des Produits :</b>", styles['Title'])  # type: ignore[name-defined]
    elements.append(title)
    elements.append(Spacer(1, 12))  # type: ignore[name-defined]

    desc_style = ParagraphStyle(  # type: ignore[name-defined]
        'description',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        alignment=4,
    )

    data = [["Nom du produit", "Type de produit", "Description", "Quantité", "Date d'ajout"]]

    for produit in produits:
        description = produit.description or ""
        if len(description) > 300:
            description = description[:300] + "..."

        data.append([
            produit.nom_produit,
            produit.type_produit,
            Paragraph(description, desc_style),  # type: ignore[name-defined]
            produit.quantite_stock,
            produit.date_ajout.strftime('%d/%m/%Y'),
        ])

    col_widths = [100, 100, 350, 100, 100]
    table = Table(data, colWidths=col_widths, repeatRows=1)  # type: ignore[name-defined]

    table.setStyle(TableStyle([  # type: ignore[name-defined]
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),  # type: ignore[name-defined]
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),            # type: ignore[name-defined]
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),                # type: ignore[name-defined]
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),          # type: ignore[name-defined]
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),                 # type: ignore[name-defined]
    ]))

    elements.append(table)
    doc.build(elements)  # type: ignore[name-defined]
    return response


def verifier_stock(request):
    produits = _produits_for_user(request.user)  # ✅ CORRIGÉ

    seuils = {
        'Graines': 50,
        'Médicaments': 50,
        'Matériel agricole': 5,
        'Légumes': 30,
        'Fruits': 30,
    }

    produits_insuffisants = []

    for p in produits:
        seuil = seuils.get(p.type_produit)
        if seuil is not None:
            match = re.search(r'\d+(\.\d+)?', str(p.quantite_stock))
            quantite = float(match.group()) if match else 0
            if quantite < seuil:
                produits_insuffisants.append(f"{p.nom_produit} ({p.type_produit}) : {quantite} < {seuil}")

    for notif in produits_insuffisants:
        messages.warning(request, f"Quantité insuffisante : {notif}")

    return produits_insuffisants

def index(request):
    return render(request, 'index.html')

from django.shortcuts import render
from .models import Produit

def produits(request):
    query_type = request.GET.get('type_produit', '')

    # base filtrée par ferme
    base_qs = _produits_for_user(request.user)  # ✅ CORRIGÉ

    if query_type:
        produits = base_qs.filter(type_produit__icontains=query_type)
    else:
        produits = base_qs

    context = {
        'produits': produits,
        'query_type': query_type,
        'active_page': 'produits',
    }
    return render(request, 'public/produits.html', context)