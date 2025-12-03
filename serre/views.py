from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Plantation
from .forms import PlantationForm 
from sols.models import AnalyseSol
from users.models import Farm
from datetime import datetime, timedelta
import re
from datetime import date, timedelta
import calendar
from collections import defaultdict
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def _ajouter_notification_ignoree(request, notification_id):
    """Ajoute une notification à la liste des ignorées"""
    if 'notifications_ignorees' not in request.session:
        request.session['notifications_ignorees'] = []
    
    if notification_id not in request.session['notifications_ignorees']:
        request.session['notifications_ignorees'].append(notification_id)
        request.session.modified = True
    print(f"✅ Notification {notification_id} ajoutée aux ignorées")


def _notification_est_ignoree(request, notification_id):
    """Vérifie si une notification a été ignorée"""
    notifications_ignorees = request.session.get('notifications_ignorees', [])
    return notification_id in notifications_ignorees


def supprimer_notification(request, notification_id):
    """Supprime une notification ou la marque comme ignorée - VERSION FINALE"""
    print(f"🗑️ Suppression demandée: {notification_id}")
    
    if notification_id.startswith('changement_'):
        # Pour les notifications de changement d'état, supprimer de la session
        if 'notifications_session' in request.session:
            notifications_session = request.session['notifications_session']
            nouvelles_notifications = [
                n for n in notifications_session if n.get('id') != notification_id
            ]
            request.session['notifications_session'] = nouvelles_notifications
            request.session.modified = True
            print(f"✅ Notification changement d'état supprimée: {notification_id}")
    
    else:
        # Pour les notifications d'arrosage, les marquer comme ignorées
        _ajouter_notification_ignoree(request, notification_id)
        print(f"✅ Notification arrosage ignorée: {notification_id}")
    
    return redirect('notifications')


CONSEILS_PLANTES = {
    'raisin': {
        'semée': "Arrose légèrement, le sol doit rester humide mais jamais détrempé. Température idéale : 20-25°C pour favoriser la germination.",
        'croissance': "Arrose profondément mais moins souvent pour développer de bonnes racines. Maintiens une température stable autour de 22°C et assure une bonne ventilation.",
        'floraison': "Réduis légèrement l'arrosage pour concentrer l'énergie dans les fleurs. Température idéale : 23-25°C et circulation d'air suffisante pour éviter les maladies.",
        'maturité': "Diminue l'arrosage pour concentrer le sucre dans les raisins. Température : 20-24°C. Ouvre la serre pour éviter la surchauffe.",
        'récolté': "Arrose modérément pour garder le plant en bonne santé. Taille légère pour préparer la prochaine saison. Température : 18-22°C.",
        'abîmé': "Coupe immédiatement les grappes touchées. Réduis l'humidité et assure une bonne ventilation pour éviter la propagation des champignons."
    },
    'lavande': {
        'semée': "Arrose légèrement, le sol doit être drainant et non saturé. Température : 18-22°C et lumière directe abondante.",
        'croissance': "Arrose uniquement quand le sol est sec. Température stable 20°C. Aère la serre pour éviter les moisissures.",
        'floraison': "Réduis l'arrosage pour intensifier l'arôme. Température : 20-25°C. Évite d'arroser les fleurs directement.",
        'maturité': "Laisse sécher le sol entre les arrosages. Température : 22-25°C. Un peu de chaleur directe aide à produire plus d'huiles essentielles.",
        'récolté': "Arrose très légèrement si nécessaire pour garder la plante vive. Température : 20-22°C. Stocke les tiges dans un endroit sec et aéré.",
        'abîmé': "Vérifie le drainage : excès d'eau = plante abîmée. Température : 18-22°C. Supprime les parties grises ou molles."
    },
    'fraise': {
        'semée': "Garde le sol humide mais pas détrempé. Température idéale : 18-22°C pour une bonne levée.",
        'croissance': "Arrose régulièrement au pied, jamais sur les feuilles. Température : 20°C. Ajoute du paillage pour conserver l'humidité.",
        'floraison': "Arrosage modéré pour favoriser la pollinisation. Température : 20-22°C. Aère la serre pour limiter l'humidité excessive.",
        'maturité': "Arrose légèrement mais régulièrement pour des fruits juteux. Température : 18-22°C. Vérifie les fraises tous les jours.",
        'récolté': "Arrose modérément pour prolonger la production. Température : 18-20°C. Retire les feuilles mortes.",
        'abîmé': "Enlève les fruits tachés. Arrose moins si le sol est trop humide. Température : 18-22°C. Aère la serre pour limiter la moisissure."
    },
    'persil': {
        'semée': "Sol humide mais non détrempé. Température : 18-20°C pour une germination optimale.",
        'croissance': "Arrose régulièrement sans excès. Température : 20°C. Coupe quelques feuilles pour stimuler la pousse.",
        'floraison': "Réduis l'arrosage pour éviter la montée en graine. Température : 18-20°C. Supprime les tiges florales si besoin.",
        'maturité': "Arrose modérément pour garder les feuilles vertes. Température : 18-20°C. Récolte régulièrement pour maintenir la vigueur.",
        'récolté': "Arrose légèrement pour garder le sol humide. Température : 18-20°C. Évite la chaleur excessive.",
        'abîmé': "Coupe les feuilles jaunies. Arrose moins si le sol est détrempé. Température : 18-20°C. Vérifie la qualité de l'eau."
    },
    'kiwi': {
        'semée': "Sol humide mais pas saturé. Température : 22-26°C pour favoriser la germination.",
        'croissance': "Arrose profondément pour favoriser l'enracinement. Température : 22-25°C. Installe un support solide pour la liane.",
        'floraison': "Arrose légèrement mais régulièrement. Température : 23-25°C. Assure la présence de fleurs mâles et femelles.",
        'maturité': "Réduis l'arrosage pour concentrer les sucres. Température : 20-24°C. Aère bien pour éviter les champignons.",
        'récolté': "Arrose modérément si nécessaire. Température : 18-22°C. Stocke les fruits dans un endroit frais.",
        'abîmé': "Retire les fruits fissurés. Température : 20-22°C. Diminue l'humidité pour protéger la plante."
    },
    'betterave': {
        'semée': "Sol humide mais jamais détrempé. Température : 15-20°C pour une levée uniforme.",
        'croissance': "Arrose le soir régulièrement pour maintenir la fraîcheur. Température : 18-20°C. Éclaircis les plants.",
        'floraison': "Humidité modérée, sol légèrement humide. Température : 18-20°C pour éviter les maladies.",
        'maturité': "Arrose en profondeur mais moins souvent. Température : 18-20°C. Garde le sol meuble pour de belles racines.",
        'récolté': "Arrose très légèrement si nécessaire. Température : 15-18°C. Laisse sécher avant stockage.",
        'abîmé': "Supprime les feuilles abîmées. Température : 15-20°C. Vérifie le drainage du sol."
    },
    'épinard': {
        'semée': "Sol humide mais non détrempé. Température : 10-18°C pour une bonne germination.",
        'croissance': "Arrose le soir régulièrement. Température : 15°C. Ajoute du compost pour booster la croissance.",
        'floraison': "Réduis l'arrosage pour éviter la montée en graine. Température : 12-18°C. Supprime les tiges florales.",
        'maturité': "Sol humide mais non saturé. Température : 12-18°C. Récolte les feuilles extérieures.",
        'récolté': "Arrose légèrement pour redonner de la vigueur. Température : 12-18°C. Retire les feuilles abîmées.",
        'abîmé': "Vérifie le drainage pour éviter l'eau stagnante. Température : 10-18°C. Aère bien la serre."
    },
    'haricot': {
        'semée': "Sol humide mais pas froid. Température : 18-22°C pour une germination rapide.",
        'croissance': "Arrose régulièrement, surtout en chaleur. Température : 20°C. Paillage léger pour conserver l'humidité.",
        'floraison': "Humidité constante mais pas excessive. Température : 20-22°C. Pas d'eau sur les feuilles.",
        'maturité': "Arrose légèrement pour garder les gousses tendres. Température : 20-22°C. Récolte fréquente pour stimuler la production.",
        'récolté': "Arrose modérément après récolte. Température : 18-20°C. Nettoie la base des plants.",
        'abîmé': "Supprime les feuilles malades. Température : 18-20°C. Réduis l'humidité si le feuillage jaunit."
    },
    'concombre': {
        'semée': "Sol humide mais pas saturé. Température : 22-25°C pour une bonne levée.",
        'croissance': "Arrose régulièrement, beaucoup d'eau nécessaire. Température : 22-25°C. Attache les tiges pour améliorer l'aération.",
        'floraison': "Arrosage modéré mais constant. Température : 22-25°C. Lumière suffisante pour favoriser les fleurs femelles.",
        'maturité': "Humidité constante pour éviter l'amertume. Température : 22-25°C. Récolte tôt pour des fruits tendres.",
        'récolté': "Arrose légèrement après récolte. Température : 20-22°C. Nettoie les feuilles basses.",
        'abîmé': "Retire les fruits déformés. Température : 20-22°C. Vérifie l'arrosage pour éviter des irrégularités."
    },
    'laitue': {
        'semée': "Sol humide mais jamais détrempé. Température : 12-18°C pour une bonne germination.",
        'croissance': "Arrose souvent en petite quantité. Température : 15°C. Paillage pour garder le sol frais.",
        'floraison': "Retire la tige florale pour éviter l'amertume. Température : 15-18°C. Réduis la chaleur si nécessaire.",
        'maturité': "Arrosage modéré pour éviter les feuilles molles. Température : 15-18°C. Récolte tôt pour un goût doux.",
        'récolté': "Arrose légèrement pour relancer les pousses. Température : 15°C. Nettoie les résidus autour.",
        'abîmé': "Surveille les limaces dans la serre humide. Température : 12-18°C. Aère pour limiter l'humidité."
    },
    'tomate': {
        'semée': "Lumière intense pour éviter l'étiolement. Arrosage léger et régulier. Température : 20-25°C.",
        'croissance': "Arrose profondément pour renforcer les racines. Température : 22°C. Retire les gourmands.",
        'floraison': "Secoue légèrement les branches pour la pollinisation. Arrosage régulier. Température : 22-25°C.",
        'maturité': "Arrosage constant mais pas excessif. Température : 22-25°C. Plus de lumière = fruits plus sucrés.",
        'récolté': "Arrose légèrement après récolte. Température : 20-22°C. Nettoie autour des plants.",
        'abîmé': "Enlève les feuilles touchant le sol. Température : 20-22°C. Aère la serre pour éviter le mildiou."
    },
    'carotte': {
        'semée': "Sol humide mais non détrempé. Température : 15-20°C pour une germination uniforme.",
        'croissance': "Arrose régulièrement en petite quantité. Température : 18°C. Sol meuble pour éviter les racines tordues.",
        'floraison': "Sol légèrement humide. Température : 15-20°C. Évite les fortes chaleurs.",
        'maturité': "Arrose un peu moins pour éviter les fissures. Température : 15-18°C. Vérifie la taille en déterrant légèrement.",
        'récolté': "Laisse sécher avant stockage. Température : 15-18°C. Ne lave pas immédiatement.",
        'abîmé': "Supprime les plants malades. Température : 15-18°C. Évite le sol compact et humide."
    }
}

def _detecter_changement_etat(plantation, ancien_etat, nouvel_etat):
    """Détecte si l'agriculteur a changé manuellement l'état"""
    if ancien_etat and nouvel_etat and ancien_etat != nouvel_etat:
        print(f"🔔 CHANGEMENT D'ÉTAT DÉTECTÉ: {plantation.nomCulture} - {ancien_etat} → {nouvel_etat}")
        return True
    return False

def _generer_conseil_etat(nom_plante, nouvel_etat):
    """Génère le conseil approprié quand l'état change"""
    nom_lower = nom_plante.lower()
    
    # Recherche dans les noms de plantes
    for cle_plante, conseils in CONSEILS_PLANTES.items():
        if cle_plante in nom_lower:
            conseil = conseils.get(nouvel_etat.lower(), "💡 Continuez les bonnes pratiques pour cet état.")
            return conseil
    
    return "💡 Surveillez régulièrement l'évolution de votre plante."

def _calculer_total_notifications(request):
    """Calcule le nombre total de notifications pour l'utilisateur"""
    try:
        plantations = _plantations_for_user(request.user)
        total = 0
        
        # 1. Notifications de changement d'état (session) - FILTRER IGNORÉES
        notifications_session = request.session.get('notifications_session', [])
        for notif in notifications_session:
            if not _notification_est_ignoree(request, notif.get('id')):
                total += 1
        
        # 2. Notifications d'arrosage (calculées en temps réel) - FILTRER IGNORÉES
        for plantation in plantations:
            est_en_retard, details = _verifier_tous_arrosages_retard(plantation)
            if est_en_retard:
                for retard_info in details['retards_semaine']:
                    notification_id = f"arrosage_{plantation.idSerre}_{retard_info['jours_retard']}"
                    if not _notification_est_ignoree(request, notification_id):
                        total += 1
        
        # 3. Notification calendrier (toujours présente)
        total += 1
        
        print(f"🔔 Total notifications calculé (avec filtrage): {total}")
        return total
        
    except Exception as e:
        print(f"❌ Erreur calcul notifications: {e}")
        return 0


# +++ AJOUT
def _current_farm(request):
    user = request.user
    profile = getattr(user, "profile", None)

    if profile and profile.role == "TECH" and profile.farm:
        return profile.farm

    farms = Farm.objects.filter(owner=user)
    if farms.exists():
        return farms.first()  # même logique que produits/cultures/sols
    return None

# +++ AJOUT
def _plantations_for_user(user):
    profile = getattr(user, "profile", None)
    if profile and profile.role == "TECH" and profile.farm:
        return Plantation.objects.filter(farm=profile.farm)
    elif profile and profile.role == "ADMIN":
        return Plantation.objects.filter(farm__owner=user)
    return Plantation.objects.none()

# +++ NOUVELLE FONCTION : Calcul du prochain arrosage
def _calculer_prochain_arrosage(plantation):
    """Calcule automatiquement la date du prochain arrosage"""
    if not plantation.datesIrrigation:
        return "À planifier"
    
    dates_list = plantation.datesIrrigation.strip().split('\n')
    if not dates_list:
        return "À planifier"
    
    # Récupérer la dernière date d'arrosage
    derniere_date_str = dates_list[-1].strip()
    
    try:
        # Convertir la dernière date en objet date
        derniere_date = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
        aujourdhui = timezone.now().date()
        
        # Analyser la fréquence d'arrosage
        frequence = plantation.frequenceArrosage.lower() if plantation.frequenceArrosage else ""
        
        jours_ajouter = 0
        
        if "tous les jours" in frequence or "quotidien" in frequence:
            jours_ajouter = 1
        elif "tous les 2 jours" in frequence:
            jours_ajouter = 2
        elif "tous les 3 jours" in frequence:
            jours_ajouter = 3
        elif "tous les 4 jours" in frequence:
            jours_ajouter = 4
        elif "tous les 5 jours" in frequence:
            jours_ajouter = 5
        elif "tous les 6 jours" in frequence:
            jours_ajouter = 6
        elif "hebdomadaire" in frequence or "toutes les semaines" in frequence:
            jours_ajouter = 7
        elif "tous les 15 jours" in frequence:
            jours_ajouter = 15
        else:
            # Essayer de trouver un nombre dans la fréquence
            match = re.search(r'(\d+)\s*jour', frequence)
            if match:
                jours_ajouter = int(match.group(1))
            else:
                return "À planifier"
        
        # Calculer la prochaine date
        prochaine_date = derniere_date + timedelta(days=jours_ajouter)
        
        # Vérifier si c'est aujourd'hui ou dans le futur
        if prochaine_date == aujourdhui:
            return "AUJOURD'HUI"
        elif prochaine_date < aujourdhui:
            return "EN RETARD"
        else:
            return prochaine_date.strftime("%d/%m/%Y")
            
    except ValueError:
        return "Date invalide"

# Vue pour la liste des plantations (FRONT OFFICE - accessible à tous)
def plantation_list(request):
    """Afficher toutes les plantations - FRONT OFFICE avec RECHERCHE et PAGINATION"""
    plantations = _plantations_for_user(request.user).order_by('-dateDerniereMiseAJour')
    
    # VÉRIFIER SI ON DOIT JOUER UN SON
    jouer_son = request.session.pop('jouer_son_dernier', False) if 'jouer_son_dernier' in request.session else False
    
    # CALCULER LE TOTAL DES NOTIFICATIONS
    total_notifications_global = _calculer_total_notifications(request)
    
    # RECHERCHE ET FILTRES
    query = request.GET.get('q')
    etat_filter = request.GET.get('etat')
    serre_filter = request.GET.get('serre')
    
    # Appliquer les filtres
    if query:
        plantations = plantations.filter(
            models.Q(nomCulture__icontains=query) |
            models.Q(variete__icontains=query) |
            models.Q(nomSerre__icontains=query)
        )
    
    if etat_filter:
        plantations = plantations.filter(etat=etat_filter)
    
    if serre_filter:
        plantations = plantations.filter(nomSerre__iexact=serre_filter)
    
    # ⚡ PAGINATION - 6 plantations par page
    paginator = Paginator(plantations, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Récupérer les serres uniques pour le filtre (normalisées)
    serres_uniques = Plantation.objects.filter(
        farm=_current_farm(request)
    ).values_list('nomSerre', flat=True).distinct()
    
    # Normaliser les noms de serres (première lettre en majuscule)
    serres_normalisees = []
    seen_serres = set()
    
    for serre in serres_uniques:
        if serre:  # Vérifier que la serre n'est pas vide
            serre_normalisee = serre.capitalize() if serre else serre
            if serre_normalisee not in seen_serres:
                seen_serres.add(serre_normalisee)
                serres_normalisees.append(serre_normalisee)
    
    # Trier les serres par ordre alphabétique
    serres_normalisees.sort()
    
    # Vérifier pour chaque plantation si elle a été arrosée aujourd'hui
    aujourdhui = timezone.now().strftime("%d/%m/%Y")
    for plantation in page_obj:  # ⚡ Utiliser page_obj au lieu de plantations
        plantation.deja_arrose_aujourdhui = False
        if plantation.datesIrrigation:
            dates_list = plantation.datesIrrigation.strip().split('\n')
            if dates_list and dates_list[-1].strip() == aujourdhui:
                plantation.deja_arrose_aujourdhui = True
        
        plantation.prochain_arrosage_calcule = _calculer_prochain_arrosage(plantation)
    
    context = {
        'plantations': page_obj,  # ⚡ Utiliser page_obj au lieu de plantations
        'page_obj': page_obj,     # ⚡ Pour la pagination
        'active_page': 'serre',
        'aujourdhui': aujourdhui,
        'serres_uniques': serres_normalisees,
        'search_query': query,
        'etat_filter': etat_filter,
        'serre_filter': serre_filter,
        'jouer_son_global': jouer_son,
        'total_notifications_global': total_notifications_global
    }
    return render(request, 'backoffice/plantation_list.html', context)

def plantation_create(request):
    """Créer une nouvelle plantation - BACK OFFICE"""
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES)

        farm = _current_farm(request)
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)

        if form.is_valid():
            plantation = form.save(commit=False)
            plantation.farm = _current_farm(request)
            plantation.save()
            messages.success(request, f"✅ Plantation '{plantation.nomCulture}' ajoutée avec succès!")
            return redirect('plantation_list')
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PlantationForm()
        farm = _current_farm(request)
        if farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=farm)
    
    context = {
        'form': form,
        'title': 'Ajouter une Plantation',
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_form.html', context)

def plantation_update(request, idSerre):
    """Modifier une plantation existante - AVEC DÉTECTION CHANGEMENT ÉTAT"""
    plantation = get_object_or_404(_plantations_for_user(request.user), idSerre=idSerre)
    ancien_etat = plantation.etat
    
    if request.method == 'POST':
        form = PlantationForm(request.POST, request.FILES, instance=plantation)

        if plantation.farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=plantation.farm)

        if form.is_valid():
            nouvel_etat = form.cleaned_data['etat']
            
            # ⚡ DÉTECTION CHANGEMENT D'ÉTAT
            if _detecter_changement_etat(plantation, ancien_etat, nouvel_etat):
                conseil = _generer_conseil_etat(plantation.nomCulture, nouvel_etat)
                
                # Créer la notification
                notification_etat = {
                    'type': 'changement_etat',
                    'message': f"🌱 {plantation.nomCulture} - État changé de '{ancien_etat}' à '{nouvel_etat}'",
                    'conseil': conseil,
                    'plantation_id': plantation.idSerre,
                    'date_creation': timezone.now().strftime("%d/%m/%Y %H:%M"),
                    'priorite': 'conseil',
                    'id': f"changement_{plantation.idSerre}_{timezone.now().timestamp()}"  # ID unique
                }
                
                # ⚡ AJOUTER À LA SESSION
                if 'notifications_session' not in request.session:
                    request.session['notifications_session'] = []
                
                request.session['notifications_session'].append(notification_etat)
                request.session.modified = True
                
                # ⚡ MARQUER POUR SON
                request.session['jouer_son_dernier'] = True
                request.session.modified = True
                
                print(f"🔔 NOTIFICATION CRÉÉE: {plantation.nomCulture}")
            
            form.save()
            messages.success(request, f"✅ Plantation '{plantation.nomCulture}' modifiée avec succès!")
            return redirect('plantation_list')
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PlantationForm(instance=plantation)
        if plantation.farm:
            form.fields['sol'].queryset = AnalyseSol.objects.filter(farm=plantation.farm)
    
    context = {
        'form': form,
        'title': f'Modifier {plantation.nomCulture}',
        'plantation': plantation,
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_form.html', context)

def plantation_delete(request, idSerre):
    """Supprimer une plantation - BACK OFFICE"""
    plantation = get_object_or_404(_plantations_for_user(request.user), idSerre=idSerre)
    
    if request.method == 'POST':
        nom_culture = plantation.nomCulture
        plantation.delete()
        messages.success(request, f"✅ Plantation '{nom_culture}' supprimée avec succès!")
        return redirect('plantation_list')
    
    context = {
        'plantation': plantation,
        'active_page': 'serre'
    }
    return render(request, 'backoffice/plantation_confirm_delete.html', context)

def confirmer_arrosage(request, idSerre):
    """Bouton pour confirmer l'arrosage d'aujourd'hui - RESTE SUR LA MÊME PAGE"""
    plantation = get_object_or_404(_plantations_for_user(request.user), idSerre=idSerre)
    
    # Vérifier si déjà arrosé aujourd'hui
    aujourdhui = timezone.now().strftime("%d/%m/%Y")
    if plantation.datesIrrigation:
        dates_list = plantation.datesIrrigation.strip().split('\n')
        if dates_list and dates_list[-1].strip() == aujourdhui:
            messages.warning(request, f"⚠️ {plantation.nomCulture} a déjà été arrosée aujourd'hui !")
            # RESTER sur la page actuelle
            referer = request.META.get('HTTP_REFERER', 'plantation_list')
            return redirect(referer)
    
    # Ajouter automatiquement la date d'aujourd'hui
    if plantation.datesIrrigation:
        plantation.datesIrrigation += f"\n{aujourdhui}"
    else:
        plantation.datesIrrigation = aujourdhui
        
    plantation.save()
    
    messages.success(request, f"✅ {plantation.nomCulture} arrosée aujourd'hui ({aujourdhui}) !")
    
    # RESTER sur la page actuelle au lieu de rediriger vers calendrier
    referer = request.META.get('HTTP_REFERER', 'plantation_list')
    return redirect(referer)
def serres(request):
    """Vue front-office pour afficher les serres avec RECHERCHE et PAGINATION"""
    
    if request.user.is_authenticated:
        plantations = _plantations_for_user(request.user).order_by('-dateDerniereMiseAJour')
        total_notifications_global = _calculer_total_notifications(request)
    else:
        plantations = Plantation.objects.none()
        total_notifications_global = 0
    
    # RECHERCHE FRONTOFFICE
    query = request.GET.get('q')
    if query:
        plantations = plantations.filter(
            models.Q(nomCulture__icontains=query) |
            models.Q(variete__icontains=query) |
            models.Q(nomSerre__icontains=query)
        )

    # ⚡ PAGINATION - 6 plantations par page
    paginator = Paginator(plantations, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    # Ajouter la dernière date d'irrigation pour chaque plantation
    for plantation in page_obj:  # ⚡ Utiliser page_obj au lieu de plantations
        plantation.derniere_irrigation = ""
        plantation.prochain_arrosage = _calculer_prochain_arrosage(plantation)

        if plantation.datesIrrigation:
            dates_list = plantation.datesIrrigation.strip().split('\n')
            if dates_list:
                plantation.derniere_irrigation = dates_list[-1].strip()

    context = {
        'plantations': page_obj,  # ⚡ Utiliser page_obj au lieu de plantations
        'page_obj': page_obj,     # ⚡ Pour la pagination
        'active_page': 'serres',
        'search_query': query,
        'total_notifications_global': total_notifications_global
    }
    return render(request, 'public/serres.html', context)

def logout_view(request):
    return render(request, 'logout.html')

def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')

def calendrier_semaine(request):
    plantations = _plantations_for_user(request.user)
    events = []

    aujourdhui = timezone.now().date()
    semaine_debut = aujourdhui - timedelta(days=aujourdhui.weekday())  # lundi
    semaine_fin = semaine_debut + timedelta(days=6)  # dimanche

    for p in plantations:
        prochaine = _calculer_prochain_arrosage(p)
        if isinstance(prochaine, str):
            continue
        date_arrosage = datetime.strptime(prochaine, "%d/%m/%Y").date()
        if semaine_debut <= date_arrosage <= semaine_fin:
            heure = p.heureArrosage or datetime.strptime("08:00","%H:%M").time()
            start_datetime = datetime.combine(date_arrosage, heure)

            if date_arrosage == aujourdhui:
                color = "#28a745"
            elif date_arrosage < aujourdhui:
                color = "#dc3545"
            else:
                color = "#007bff"

            events.append({
                'title': f"{p.nomCulture} ({heure.strftime('%H:%M')})",
                'start': start_datetime.isoformat(),
                'color': color,
            })

    context = {'events': events}
    return render(request, 'backoffice/calendrier_semaine.html', context)

def calendrier_semaine_front(request):
    """Calendrier frontoffice avec la MÊME logique que backoffice"""
    # Date actuelle
    aujourdhui = timezone.now().date()
    aujourdhui_str = aujourdhui.strftime("%d/%m/%Y")
    
    # Calcul de la semaine (lundi au dimanche)
    debut_semaine = aujourdhui - timedelta(days=aujourdhui.weekday())
    jours_semaine = [debut_semaine + timedelta(days=i) for i in range(7)]
    
    # Récupérer toutes les plantations de l'utilisateur
    plantations = _plantations_for_user(request.user)
    
    # Organiser par jour de la semaine
    jours_semaine_data = []
    
    for i, date_jour in enumerate(jours_semaine):
        plantations_du_jour = []
        nom_jour = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i]
        
        for plantation in plantations:
            heure_arrosage = plantation.heureArrosage.strftime("%H:%M") if plantation.heureArrosage else "08:00"
            
            # Vérifier si arrosée à cette date
            arrosee_ce_jour = False
            if plantation.datesIrrigation:
                dates_list = [d.strip() for d in plantation.datesIrrigation.split('\n') if d.strip()]
                for date_str in dates_list:
                    try:
                        date_arrosage = datetime.strptime(date_str, "%d/%m/%Y").date()
                        if date_arrosage == date_jour:
                            arrosee_ce_jour = True
                            break
                    except:
                        continue
            
            # Calculer la fréquence
            frequence = plantation.frequenceArrosage or ""
            if "2 jours" in frequence:
                intervalle = 2
            elif "3 jours" in frequence:
                intervalle = 3
            elif "4 jours" in frequence:
                intervalle = 4
            elif "5 jours" in frequence:
                intervalle = 5
            elif "6 jours" in frequence:
                intervalle = 6
            elif "semaine" in frequence or "7 jours" in frequence:
                intervalle = 7
            elif "15 jours" in frequence:
                intervalle = 15
            else:
                intervalle = 2  # Par défaut
            
            # Trouver la dernière date d'arrosage pour calculer la série
            derniere_irrigation = None
            if plantation.datesIrrigation:
                dates_list = [d.strip() for d in plantation.datesIrrigation.split('\n') if d.strip()]
                if dates_list:
                    try:
                        derniere_date_str = dates_list[-1]
                        derniere_irrigation = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
                    except:
                        derniere_irrigation = plantation.dateSemis
            else:
                derniere_irrigation = plantation.dateSemis
            
            if not derniere_irrigation:
                continue
            
            # Générer toutes les dates d'arrosage pour la semaine
            date_courante = derniere_irrigation
            dates_arrosage_calculees = []
            
            # Remonter dans le passé pour trouver le premier arrosage de la série
            while date_courante >= debut_semaine - timedelta(days=intervalle * 2):
                dates_arrosage_calculees.append(date_courante)
                date_courante -= timedelta(days=intervalle)
            
            # Maintenant avancer pour couvrir la semaine
            date_courante = derniere_irrigation
            while date_courante <= jours_semaine[-1]:
                if date_courante not in dates_arrosage_calculees:
                    dates_arrosage_calculees.append(date_courante)
                date_courante += timedelta(days=intervalle)
            
            # Trier les dates
            dates_arrosage_calculees.sort()
            
            # Vérifier si cette date fait partie des arrosages calculés
            for date_calculee in dates_arrosage_calculees:
                if date_calculee == date_jour:
                    plante_info = {
                        'plantation': plantation,
                        'heure': heure_arrosage,
                        'heure_tri': heure_arrosage,
                        'deja_arrose': arrosee_ce_jour,
                        'statut': 'futur'  # Par défaut
                    }
                    
                    # DÉTERMINER LE STATUT EXACT (MÊME LOGIQUE QUE BACKOFFICE)
                    if arrosee_ce_jour:
                        plante_info['statut'] = 'deja_arrose'
                        plante_info['type_arrosage'] = 'Déjà arrosé'
                    elif date_jour < aujourdhui:
                        plante_info['statut'] = 'retard'
                        plante_info['type_arrosage'] = 'Arrosage retard'
                    elif date_jour == aujourdhui:
                        plante_info['statut'] = 'aujourdhui'
                        plante_info['type_arrosage'] = 'Arrosage aujourd\'hui'
                    else:
                        plante_info['statut'] = 'futur'
                        plante_info['type_arrosage'] = 'Futur arrosage'
                    
                    plantations_du_jour.append(plante_info)
                    break
        
        # Trier par heure pour chaque jour
        plantations_du_jour.sort(key=lambda x: x['heure_tri'])
        
        jours_semaine_data.append({
            'date': date_jour,
            'plantations': plantations_du_jour,
            'nom_jour': nom_jour
        })
    
    context = {
        'jours_semaine': jours_semaine_data,
        'semaine_du': debut_semaine.strftime("%d/%m/%Y"),
        'semaine_au': jours_semaine[-1].strftime("%d/%m/%Y"),
        'aujourdhui': aujourdhui,
        'page_title': '📅 Calendrier des Arrosages'
    }
    return render(request, 'public/calendrier_semaine.html', context)

def calendrier_backoffice(request):
    """Calendrier hebdomadaire des arrosages - VERSION COMPLÈTE"""
    # Date actuelle
    aujourdhui = timezone.now().date()
    aujourdhui_str = aujourdhui.strftime("%d/%m/%Y")
    
    # Calcul de la semaine (lundi au dimanche)
    debut_semaine = aujourdhui - timedelta(days=aujourdhui.weekday())
    jours_semaine = [debut_semaine + timedelta(days=i) for i in range(7)]
    
    # Récupérer toutes les plantations de l'utilisateur
    plantations = _plantations_for_user(request.user)
    
    # Organiser par jour de la semaine
    jours_semaine_data = []
    
    for i, date_jour in enumerate(jours_semaine):
        plantations_du_jour = []
        nom_jour = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i]
        
        for plantation in plantations:
            heure_arrosage = plantation.heureArrosage.strftime("%H:%M") if plantation.heureArrosage else "08:00"
            
            # Vérifier si arrosée à cette date
            arrosee_ce_jour = False
            if plantation.datesIrrigation:
                dates_list = [d.strip() for d in plantation.datesIrrigation.split('\n') if d.strip()]
                for date_str in dates_list:
                    try:
                        date_arrosage = datetime.strptime(date_str, "%d/%m/%Y").date()
                        if date_arrosage == date_jour:
                            arrosee_ce_jour = True
                            break
                    except:
                        continue
            
            # Calculer la fréquence
            frequence = plantation.frequenceArrosage or ""
            if "2 jours" in frequence:
                intervalle = 2
            elif "3 jours" in frequence:
                intervalle = 3
            elif "4 jours" in frequence:
                intervalle = 4
            elif "5 jours" in frequence:
                intervalle = 5
            elif "6 jours" in frequence:
                intervalle = 6
            elif "semaine" in frequence or "7 jours" in frequence:
                intervalle = 7
            elif "15 jours" in frequence:
                intervalle = 15
            else:
                intervalle = 2  # Par défaut
            
            # Trouver la dernière date d'arrosage pour calculer la série
            derniere_irrigation = None
            if plantation.datesIrrigation:
                dates_list = [d.strip() for d in plantation.datesIrrigation.split('\n') if d.strip()]
                if dates_list:
                    try:
                        derniere_date_str = dates_list[-1]
                        derniere_irrigation = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
                    except:
                        derniere_irrigation = plantation.dateSemis
            else:
                derniere_irrigation = plantation.dateSemis
            
            if not derniere_irrigation:
                continue
            
            # Générer toutes les dates d'arrosage pour la semaine
            date_courante = derniere_irrigation
            dates_arrosage_calculees = []
            
            # Remonter dans le passé pour trouver le premier arrosage de la série
            while date_courante >= debut_semaine - timedelta(days=intervalle * 2):
                dates_arrosage_calculees.append(date_courante)
                date_courante -= timedelta(days=intervalle)
            
            # Maintenant avancer pour couvrir la semaine
            date_courante = derniere_irrigation
            while date_courante <= jours_semaine[-1]:
                if date_courante not in dates_arrosage_calculees:
                    dates_arrosage_calculees.append(date_courante)
                date_courante += timedelta(days=intervalle)
            
            # Trier les dates
            dates_arrosage_calculees.sort()
            
            # Vérifier si cette date fait partie des arrosages calculés
            for date_calculee in dates_arrosage_calculees:
                if date_calculee == date_jour:
                    plante_info = {
                        'plantation': plantation,
                        'heure': heure_arrosage,
                        'heure_tri': heure_arrosage,
                        'deja_arrose': arrosee_ce_jour,
                        'statut': 'futur'  # Par défaut
                    }
                    
                    # DÉTERMINER LE STATUT EXACT
                    if arrosee_ce_jour:
                        plante_info['statut'] = 'deja_arrose'
                        plante_info['type_arrosage'] = 'Déjà arrosé'
                    elif date_jour < aujourdhui:
                        plante_info['statut'] = 'retard'
                        plante_info['type_arrosage'] = 'Arrosage retard'
                    elif date_jour == aujourdhui:
                        plante_info['statut'] = 'aujourdhui'
                        plante_info['type_arrosage'] = 'Arrosage aujourd\'hui'
                    else:
                        plante_info['statut'] = 'futur'
                        plante_info['type_arrosage'] = 'Futur arrosage'
                    
                    plantations_du_jour.append(plante_info)
                    break
        
        # Trier par heure pour chaque jour
        plantations_du_jour.sort(key=lambda x: x['heure_tri'])
        
        jours_semaine_data.append({
            'date': date_jour,
            'plantations': plantations_du_jour,
            'nom_jour': nom_jour
        })
    
    context = {
        'jours_semaine': jours_semaine_data,
        'semaine_du': debut_semaine.strftime("%d/%m/%Y"),
        'semaine_au': jours_semaine[-1].strftime("%d/%m/%Y"),
        'aujourdhui': aujourdhui,
        'page_title': '📅 Calendrier des Arrosages'
    }
    return render(request, 'backoffice/calendrier_backoffice.html', context)



def statistiques(request):
    """Page avec les 2 types de statistiques + données détaillées"""
    plantations = _plantations_for_user(request.user)
    total = plantations.count()
    
    # 1. Calcul des statistiques par état
    stats_etat = {}
    etats = ['Semée', 'Croissance', 'Floraison', 'Maturité', 'Récoltée']
    
    for etat in etats:
        count = plantations.filter(etat=etat).count()
        if count > 0:
            pourcentage = (count / total) * 100 if total > 0 else 0
            stats_etat[etat] = {
                'count': count,
                'pourcentage': round(pourcentage, 1)
            }
    
    # 2. Calcul des statistiques par type
    stats_type = {}
    mapping_categories = {
        'Légume Fruit': [
            'tomate', 'concombre', 'poivron', 'aubergine', 'courgette', 
            'piment', 'melon', 'pastèque', 'cornichon', 'courge',
            'potiron', 'potimarron', 'butternut', 'haricot', 'pois',
            'fève', 'gombo', 'okra', 'pâtisson'
        ],
        'Légume Feuille': [
            'laitue', 'épinard', 'chou', 'salade',  
            'roquette', 'mâche', 'céleri', 'oseille', 'chardon',
            'pissenlit', 'pourpier', 'arroche', 'chou kale', 'chou frisé',
            'chou rave', 'chou chinois', 'pak choi', 'cardon'
        ],
        'Légume Racine': [
            'carotte', 'radis', 'betterave', 'navet', 'panais',
            'céleri rave', 'rutabaga', 'topinambour', 'crosne',
            'raifort', 'salsifis', 'scorsonère', 'chervis', 'persil tubéreux'
        ],
        'Légume Bulbe': [
            'oignon', 'ail', 'échalote', 'poireau', 'ciboule',
            'ciboulette', 'fenouil', 'asperge', 'artichaut'
        ],
        'Aromatique': [
            'basilic', 'persil', 'menthe', 'romarin', 'thym',
            'ciboulette', 'coriandre', 'aneth', 'sarriette',
            'estragon', 'cerfeuil', 'livèche', 'marjolaine', 'origan',
            'sauge', 'verveine', 'laurier', 'curcuma', 'gingembre'
        ],
        'Fruit Arbre': [
            'pomme', 'poire', 'prune', 'cerise', 'abricot',
            'pêche', 'nectarine', 'figue', 'kiwi', 'raisin',
            'framboise', 'mûre', 'myrtille', 'groseille', 'cassis',
            'fraise', 'melon', 'pastèque'
        ],
        'Céréale': [
            'blé', 'maïs', 'orge', 'avoine', 'seigle',
            'riz', 'sarrasin', 'quinoa', 'millet', 'épeautre'
        ],
        'Fleur Comestible': [
            'capucine', 'souci', 'pensée', 'viola', 'bourrache',
            'hémérocalle', 'lavande', 'rose', 'violette'
        ]
    }
    
    categories_count = {cat: 0 for cat in mapping_categories.keys()}
    categories_count['Autre'] = 0
    
    for plantation in plantations:
        nom_lower = plantation.nomCulture.lower().strip()
        categorie_trouvee = 'Autre'
        
        for categorie, mots_cles in mapping_categories.items():
            if any(mot in nom_lower for mot in mots_cles):
                categorie_trouvee = categorie
                break
        
        categories_count[categorie_trouvee] += 1
    
    # Convertir en format avec pourcentages
    for categorie, count in categories_count.items():
        if count > 0:
            pourcentage = (count / total) * 100 if total > 0 else 0
            stats_type[categorie] = {
                'count': count,
                'pourcentage': round(pourcentage, 1)
            }
    
    # 3. Données détaillées pour l'interactivité
    plantations_par_etat = {}
    plantations_par_type = {}
    
    # Groupement par état
    for etat in etats:
        plantations_par_etat[etat] = list(plantations.filter(etat=etat).values(
            'idSerre', 'nomCulture', 'variete', 'nomSerre', 'nombrePlantes', 'etat'
        ))
    
    # Groupement par type
    for categorie, mots_cles in mapping_categories.items():
        plantations_filtrees = []
        for plantation in plantations:
            nom_lower = plantation.nomCulture.lower()
            if any(mot in nom_lower for mot in mots_cles) or (categorie == 'Autre' and not any(any(mot in nom_lower for mot in mots) for mots in mapping_categories.values() if categorie != 'Autre')):
                plantations_filtrees.append({
                    'idSerre': plantation.idSerre,
                    'nomCulture': plantation.nomCulture,
                    'variete': plantation.variete,
                    'nomSerre': plantation.nomSerre,
                    'nombrePlantes': plantation.nombrePlantes,
                    'etat': plantation.etat
                })
        plantations_par_type[categorie] = plantations_filtrees
    
    # Ajouter la catégorie "Autre"
    plantations_autre = []
    for plantation in plantations:
        nom_lower = plantation.nomCulture.lower()
        if not any(any(mot in nom_lower for mot in mots) for mots in mapping_categories.values()):
            plantations_autre.append({
                'idSerre': plantation.idSerre,
                'nomCulture': plantation.nomCulture,
                'variete': plantation.variete,
                'nomSerre': plantation.nomSerre,
                'nombrePlantes': plantation.nombrePlantes,
                'etat': plantation.etat
            })
    plantations_par_type['Autre'] = plantations_autre
    
    context = {
        'stats_etat': stats_etat,
        'stats_type': stats_type,
        'total_plantations': total,
        'plantations_par_etat': plantations_par_etat,
        'plantations_par_type': plantations_par_type,
    }
    return render(request, 'backoffice/statistiques.html', context)

def statistiques_details(request, type_stat, categorie):
    """Page détaillée quand on clique sur un élément du camembert"""
    plantations = _plantations_for_user(request.user)
    
    if type_stat == 'etat':
        plantations_filtrees = plantations.filter(etat=categorie)
        titre = f"Plantations - État: {categorie}"
    elif type_stat == 'type':
        # MÊME MAPPING EXACT que dans la vue statistiques
        mapping_categories = {
            'Légume Fruit': [
                'tomate', 'concombre', 'poivron', 'aubergine', 'courgette', 
                'piment', 'melon', 'pastèque', 'cornichon', 'courge',
                'potiron', 'potimarron', 'butternut', 'haricot', 'pois',
                'fève', 'gombo', 'okra', 'pâtisson'
            ],
            'Légume Feuille': [
                'laitue', 'épinard', 'chou', 'salade', 'blette', 
                'roquette', 'mâche', 'céleri', 'oseille', 'chardon',
                'pissenlit', 'pourpier', 'arroche', 'chou kale', 'chou frisé',
                'chou rave', 'chou chinois', 'pak choi', 'cardon'
            ],
            'Légume Racine': [
                'carotte', 'radis', 'betterave', 'navet', 'panais',
                'céleri rave', 'rutabaga', 'topinambour', 'crosne',
                'raifort', 'salsifis', 'scorsonère', 'chervis', 'persil tubéreux'
            ],
            'Légume Bulbe': [
                'oignon', 'ail', 'échalote', 'poireau', 'ciboule',
                'ciboulette', 'fenouil', 'asperge', 'artichaut'
            ],
            'Aromatique': [
                'basilic', 'persil', 'menthe', 'romarin', 'thym',
                'ciboulette', 'coriandre', 'aneth', 'sarriette',
                'estragon', 'cerfeuil', 'livèche', 'marjolaine', 'origan',
                'sauge', 'verveine', 'laurier', 'curcuma', 'gingembre'
            ],
            'Fruit Arbre': [
                'pomme', 'poire', 'prune', 'cerise', 'abricot',
                'pêche', 'nectarine', 'figue', 'kiwi', 'raisin',
                'framboise', 'mûre', 'myrtille', 'groseille', 'cassis',
                'fraise', 'melon', 'pastèque'
            ],
            'Céréale': [
                'blé', 'maïs', 'orge', 'avoine', 'seigle',
                'riz', 'sarrasin', 'quinoa', 'millet', 'épeautre'
            ],
            'Fleur Comestible': [
                'capucine', 'souci', 'pensée', 'viola', 'bourrache',
                'hémérocalle', 'lavande', 'rose', 'violette'
            ]
        }
        
        mots_cles = mapping_categories.get(categorie, [])
        
        # Méthode robuste : filtrer comme dans la vue principale
        plantations_list = []
        for plantation in plantations:
            nom_lower = plantation.nomCulture.lower().strip()
            if any(mot in nom_lower for mot in mots_cles):
                plantations_list.append(plantation)
        
        plantations_filtrees = plantations_list
        titre = f"Plantations - Type: {categorie}"
    else:
        plantations_filtrees = list(plantations)
        titre = "Toutes les plantations"
    
    # Gérer le count pour les listes et les QuerySets
    if isinstance(plantations_filtrees, list):
        total_count = len(plantations_filtrees)
    else:
        total_count = plantations_filtrees.count()
    
    context = {
        'plantations': plantations_filtrees,
        'titre': titre,
        'categorie': categorie,
        'type_stat': type_stat,
        'total': total_count
    }
    return render(request, 'backoffice/statistiques_details.html', context)


def notifications(request):
    """Page des notifications - COMBINE ARROSAGE + CHANGEMENT ÉTAT"""
    
    notifications_list = []
    plantations = _plantations_for_user(request.user)
    aujourdhui = timezone.now().date()
    
    print(f"🔔 DEBUG - Analyse de {plantations.count()} plantations")

    # 1. NOTIFICATIONS D'ARROSAGE (EXISTANT) - FILTRER LES IGNORÉES
    for plantation in plantations:
        est_en_retard, details = _verifier_tous_arrosages_retard(plantation)
        
        if est_en_retard:
            for retard_info in details['retards_semaine']:
                jours_retard = retard_info['jours_retard']
                notification_id = f"arrosage_{plantation.idSerre}_{jours_retard}"
                
                # ⚡ VÉRIFIER SI LA NOTIFICATION N'EST PAS IGNORÉE
                if _notification_est_ignoree(request, notification_id):
                    print(f"🔕 Notification ignorée, sautée: {notification_id}")
                    continue
                
                if jours_retard > 3:
                    message = f"🔴 ARROSAGE ANCIEN NON EFFECTUÉ - {plantation.nomCulture}"
                    priorite = 'critique'
                elif jours_retard == 0:
                    message = f"🟡 ARROSAGE AUJOURD'HUI - {plantation.nomCulture}"
                    priorite = 'haute'
                elif jours_retard == 1:
                    message = f"🟠 ARROSAGE HIER - {plantation.nomCulture} (1 jour)"
                    priorite = 'moyenne'
                else:
                    message = f"🔴 ARROSAGE EN RETARD - {plantation.nomCulture} ({jours_retard} jours)"
                    priorite = 'haute'
                
                notifications_list.append({
                    'type': 'arrosage',
                    'message': message,
                    'plantation': plantation,
                    'priorite': priorite,
                    'jours_retard': jours_retard,
                    'date_creation': timezone.now().strftime("%d/%m/%Y %H:%M"),
                    'id': notification_id
                })

    # 2. NOTIFICATIONS DE CHANGEMENT D'ÉTAT (SESSION) - FILTRER LES IGNORÉES
    notifications_session = request.session.get('notifications_session', [])
    
    for notif in notifications_session:
        try:
            plantation = Plantation.objects.get(idSerre=notif.get('plantation_id'))
            notification_id = notif.get('id')
            
            # ⚡ VÉRIFIER SI LA NOTIFICATION N'EST PAS IGNORÉE
            if _notification_est_ignoree(request, notification_id):
                print(f"🔕 Notification changement ignorée, sautée: {notification_id}")
                continue
            
            notifications_list.append({
                'type': 'changement_etat',
                'message': notif['message'],
                'conseil': notif['conseil'],
                'plantation_id': notif['plantation_id'],
                'plantation': plantation,
                'priorite': 'conseil',
                'date_creation': notif['date_creation'],
                'id': notification_id
            })
                
        except Plantation.DoesNotExist:
            continue
    
    # 3. NOTIFICATION CALENDRIER (toujours affichée)
    notifications_list.append({
        'type': 'info',
        'message': "📅 Pensez à consulter le calendrier pour préparer les arrosages !",
        'priorite': 'info',
        'date_creation': timezone.now().strftime("%d/%m/%Y %H:%M"),
        'id': 'calendrier_info'
    })

    # TRI PAR PRIORITÉ
    ordre_priorite = {'critique': 0, 'haute': 1, 'moyenne': 2, 'conseil': 3, 'info': 4}
    notifications_list.sort(key=lambda x: (
        ordre_priorite[x['priorite']],
        -x.get('jours_retard', 0)
    ))

    # VÉRIFIER SI ON DOIT JOUER UN SON
    jouer_son = request.session.pop('jouer_son_dernier', False) if 'jouer_son_dernier' in request.session else False

    context = {
        'notifications': notifications_list,
        'total_notifications': len(notifications_list),
        'aujourdhui': aujourdhui.strftime("%d/%m/%Y"),
        'jouer_son': jouer_son
    }
    return render(request, 'backoffice/notifications.html', context)


def _verifier_tous_arrosages_retard(plantation):
    """
    Vérifie TOUS les arrosages en retard depuis 60 jours
    Version SIMPLIFIÉE et EFFICACE
    """
    aujourdhui = timezone.now().date()
    details = {'retards_semaine': []}
    
    print(f"   🔍 Analyse {plantation.nomCulture}")
    print(f"   📅 Aujourd'hui: {aujourdhui}")
    
    # 1. SI JAMAIS ARROSÉE
    if not plantation.datesIrrigation or not plantation.datesIrrigation.strip():
        print(f"   💧 Jamais arrosée")
        if plantation.dateSemis:
            jours_sans_arrosage = (aujourdhui - plantation.dateSemis).days
            print(f"   🌱 Depuis semis: {jours_sans_arrosage} jours")
            
            if jours_sans_arrosage >= 2:
                details['retards_semaine'].append({
                    'date': plantation.dateSemis,
                    'jours_retard': jours_sans_arrosage,
                    'type': 'jamais_arrosee'
                })
        return len(details['retards_semaine']) > 0, details
    
    try:
        # 2. PLANTATION DÉJÀ ARROSÉE
        dates_list = [d.strip() for d in plantation.datesIrrigation.split('\n') if d.strip()]
        if not dates_list:
            return False, details
            
        derniere_date_str = dates_list[-1]
        derniere_date = datetime.strptime(derniere_date_str, "%d/%m/%Y").date()
        
        print(f"   💦 Dernier arrosage: {derniere_date}")
        print(f"   ⏱️ Fréquence: {plantation.frequenceArrosage}")
        
        # Calculer la fréquence
        frequence_jours = _determiner_frequence_jours(plantation.frequenceArrosage)
        print(f"   📊 Fréquence calculée: {frequence_jours} jours")
        
        # 3. GÉNÉRER TOUTES LES DATES ATTENDUES DEPUIS 60 JOURS
        date_debut_recherche = aujourdhui - timedelta(days=60)  # 2 mois en arrière
        date_courante = derniere_date + timedelta(days=frequence_jours)
        
        print(f"   🔎 Recherche depuis: {date_debut_recherche} jusqu'à: {aujourdhui}")
        
        # Liste de toutes les dates où la plantation aurait dû être arrosée
        dates_attendues = []
        while date_courante <= aujourdhui:  # Toutes les dates jusqu'à aujourd'hui
            dates_attendues.append(date_courante)
            date_courante += timedelta(days=frequence_jours)
        
        print(f"   📅 Dates attendues trouvées: {len(dates_attendues)}")
        
        # 4. VÉRIFIER CHAQUE DATE ATTENDUE
        for date_attendue in dates_attendues:
            arrosee_ce_jour = False
            
            # Vérifier si arrosée à cette date exacte
            for date_arrosage_str in dates_list:
                try:
                    date_arrosage = datetime.strptime(date_arrosage_str, "%d/%m/%Y").date()
                    if date_arrosage == date_attendue:
                        arrosee_ce_jour = True
                        break
                except:
                    continue
            
            # Si NON arrosée à cette date, c'est un retard
            if not arrosee_ce_jour:
                jours_retard = (aujourdhui - date_attendue).days
                print(f"   ❌ RETARD TROUVÉ: {date_attendue} ({jours_retard} jours de retard)")
                
                details['retards_semaine'].append({
                    'date': date_attendue,
                    'jours_retard': jours_retard,
                    'type': 'non_arrosee'
                })
        
        print(f"   📊 Total retards pour {plantation.nomCulture}: {len(details['retards_semaine'])}")
                    
    except Exception as e:
        print(f"❌ Erreur vérification retard {plantation.nomCulture}: {e}")
    
    return len(details['retards_semaine']) > 0, details

def _determiner_frequence_jours(frequence):
    """Détermine la fréquence en jours à partir du texte - UNE SEULE FOIS"""
    if not frequence:
        return 2  # Fréquence par défaut
        
    freq_lower = frequence.lower()
    
    if "tous les jours" in freq_lower or "quotidien" in freq_lower:
        return 1
    elif "2 jours" in freq_lower:
        return 2
    elif "3 jours" in freq_lower:
        return 3
    elif "4 jours" in freq_lower:
        return 4
    elif "5 jours" in freq_lower:
        return 5
    elif "6 jours" in freq_lower:
        return 6
    elif "semaine" in freq_lower or "7 jours" in freq_lower:
        return 7
    elif "15 jours" in freq_lower:
        return 15
    else:
        # Essayer de trouver un nombre dans le texte
        import re
        match = re.search(r'(\d+)\s*jour', freq_lower)
        if match:
            return int(match.group(1))
        return 2  # Fréquence par défaut

def notifications_front(request):
    """Page des notifications frontoffice - VERSION CORRIGÉE AVEC CONSEILS"""
    
    notifications_list = []
    plantations = _plantations_for_user(request.user)
    aujourdhui = timezone.now().date()
    
    print(f"🔔 DEBUG FRONT - Analyse de {plantations.count()} plantations")

    # 1. NOTIFICATIONS D'ARROSAGE - FILTRER LES IGNORÉES
    for plantation in plantations:
        est_en_retard, details = _verifier_tous_arrosages_retard(plantation)
        
        if est_en_retard:
            for retard_info in details['retards_semaine']:
                jours_retard = retard_info['jours_retard']
                notification_id = f"arrosage_{plantation.idSerre}_{jours_retard}"
                
                # Vérifier si la notification n'est pas ignorée
                if _notification_est_ignoree(request, notification_id):
                    print(f"🔕 Notification ignorée, sautée: {notification_id}")
                    continue
                
                if jours_retard > 3:
                    message = f"🔴 ARROSAGE ANCIEN NON EFFECTUÉ - {plantation.nomCulture}"
                    priorite = 'critique'
                elif jours_retard == 0:
                    message = f"🟡 ARROSAGE AUJOURD'HUI - {plantation.nomCulture}"
                    priorite = 'haute'
                elif jours_retard == 1:
                    message = f"🟠 ARROSAGE HIER - {plantation.nomCulture} (1 jour)"
                    priorite = 'moyenne'
                else:
                    message = f"🔴 ARROSAGE EN RETARD - {plantation.nomCulture} ({jours_retard} jours)"
                    priorite = 'haute'
                
                notifications_list.append({
                    'type': 'arrosage',
                    'message': message,
                    'plantation': plantation,
                    'priorite': priorite,
                    'jours_retard': jours_retard,
                    'date_creation': timezone.now().strftime("%d/%m/%Y %H:%M"),
                    'id': notification_id
                })

    # 2. NOTIFICATIONS DE CHANGEMENT D'ÉTAT - FILTRER LES IGNORÉES
    notifications_session = request.session.get('notifications_session', [])
    
    for notif in notifications_session:
        try:
            plantation = Plantation.objects.get(idSerre=notif.get('plantation_id'))
            notification_id = notif.get('id')
            
            # Vérifier si la notification n'est pas ignorée
            if _notification_est_ignoree(request, notification_id):
                print(f"🔕 Notification changement ignorée, sautée: {notification_id}")
                continue
            
            # ⚡ BIEN INCLURE LE CONSEIL
            notifications_list.append({
                'type': 'changement_etat',
                'message': notif['message'],
                'conseil': notif['conseil'],  # ⚡ IMPORTANT : NE PAS OUBLIER LE CONSEIL
                'plantation_id': notif['plantation_id'],
                'plantation': plantation,
                'priorite': 'conseil',
                'date_creation': notif['date_creation'],
                'id': notification_id
            })
            print(f"🌱 Notification changement d'état ajoutée: {notif['message']}")
                
        except Plantation.DoesNotExist:
            continue
    
    # 3. NOTIFICATION CALENDRIER
    notifications_list.append({
        'type': 'info',
        'message': "📅 Consultez le calendrier pour les prochains arrosages !",
        'priorite': 'info',
        'date_creation': timezone.now().strftime("%d/%m/%Y %H:%M"),
        'id': 'calendrier_info'
    })

    # TRI PAR PRIORITÉ
    ordre_priorite = {'critique': 0, 'haute': 1, 'moyenne': 2, 'conseil': 3, 'info': 4}
    notifications_list.sort(key=lambda x: (
        ordre_priorite[x['priorite']],
        -x.get('jours_retard', 0)
    ))

    context = {
        'notifications': notifications_list,
        'total_notifications': len(notifications_list),
        'aujourdhui': aujourdhui.strftime("%d/%m/%Y"),
        'is_frontoffice': True
    }
    return render(request, 'public/notifications_front.html', context)

def _jouer_son_notification(request):
    """Marque qu'un son doit être joué pour les notifications"""
    request.session['jouer_son_notification'] = True
    request.session.modified = True