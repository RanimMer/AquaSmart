from django.shortcuts import render, get_object_or_404, redirect
from .models import Produit
from .forms import ProduitForm
from django.db.models import Count
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet ,ParagraphStyle
import re
from django.db.models import Q
from django.contrib import messages 

# Dashboard existant
def dashboard(request):
    return render(request, 'backoffice/dashboard.html')


# Gestion Produits : affichage liste
def gestion_produits(request):
    sort = request.GET.get('sort', '')
    query = request.GET.get('query', '').strip()

    # On récupère tous les produits
    produits = Produit.objects.all()

    # --------------------
    # Filtrage par recherche
    # --------------------
    if query:
        produits = produits.filter(
            Q(nom_produit__icontains=query) |
            Q(type_produit__icontains=query) |
            Q(description__icontains=query)
        )

    # --------------------
    # Tri côté Python si nécessaire (asc / desc sur quantite_stock)
    # --------------------
    def extract_number(quantite):
        """Extrait la première valeur numérique d'une chaîne comme '25 kg' -> 25.0"""
        match = re.search(r'\d+(\.\d+)?', str(quantite))
        return float(match.group()) if match else 0

    produits = list(produits)
    if sort == 'asc':
        produits.sort(key=lambda p: extract_number(p.quantite_stock))
    elif sort == 'desc':
        produits.sort(key=lambda p: extract_number(p.quantite_stock), reverse=True)

    # --------------------
    # Vérification des seuils et notifications
    # --------------------
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
                messages.warning(request, f"Quantité insuffisante : {p.nom_produit} ({p.type_produit}) → {quantite} < {seuil}")

    # --------------------
    # Rendu du template
    # --------------------
    return render(request, 'backoffice/gestion_produits.html', {
        'produits': produits,
        'query': query,
        'sort': sort
    })



# Ajouter un produit
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gestion_produits')
    else:
        form = ProduitForm()
    return render(request, 'backoffice/form_produit.html', {'form': form, 'action': 'Ajouter'})

# Modifier un produit
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            return redirect('gestion_produits')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'backoffice/form_produit.html', {'form': form, 'action': 'Modifier'})

# Supprimer un produit
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        return redirect('gestion_produits')
    return render(request, 'backoffice/supprimer_produit.html', {'produit': produit})

# Statistiques d'un produit
def statistiques_produits(request):
    stats = Produit.objects.values('type_produit').annotate(total=Count('id'))

    labels = [item['type_produit'] for item in stats]
    values = [item['total'] for item in stats]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%')
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graph = base64.b64encode(image_png).decode('utf-8')
    return render(request, 'backoffice/statistiques_produits.html', {'graph': graph})

# PDF d'un produit
def export_pdf_produits(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="liste_produits.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    # Style du titre
    title = Paragraph("<b>Liste des Produits :</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Styles personnalisés
    desc_style = ParagraphStyle(
        'description',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        alignment=4,  # Justifié
    )

    # En-têtes du tableau
    data = [["Nom du produit", "Type de produit", "Description", "Quantité", "Date d'ajout"]]

    # Récupérer les produits
    produits = Produit.objects.all()

    for produit in produits:
        # Tronquer la description si trop longue
        description = produit.description
        if len(description) > 300:
            description = description[:300] + "..."

        data.append([
            produit.nom_produit,
            produit.type_produit,
            Paragraph(description, desc_style),
            produit.quantite_stock,
            produit.date_ajout.strftime('%d/%m/%Y'),
        ])

    # Largeurs ajustées pour que tout tienne sur une page
    col_widths = [100, 100, 350, 100, 100]

    # Création du tableau
    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Style du tableau
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Lignes du tableau
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    return response

def verifier_stock(request):
    # Récupérer tous les produits
    produits = Produit.objects.all()

    # Définir les seuils par type de produit
    seuils = {
        'Graines': 50,
        'Médicaments': 50,
        'Matériel agricole': 5,
        'Légumes': 30,
        'Fruits': 30,
    }

    # Liste pour stocker les produits insuffisants
    produits_insuffisants = []

    for p in produits:
        seuil = seuils.get(p.type_produit)
        if seuil is not None:
            # Extraire la quantité numérique si nécessaire
            import re
            match = re.search(r'\d+(\.\d+)?', str(p.quantite_stock))
            quantite = float(match.group()) if match else 0
            if quantite < seuil:
                produits_insuffisants.append(f"{p.nom_produit} ({p.type_produit}) : {quantite} < {seuil}")

    # Ajouter les notifications via messages framework
    for notif in produits_insuffisants:
        messages.warning(request, f"Quantité insuffisante : {notif}")

    return produits_insuffisants


