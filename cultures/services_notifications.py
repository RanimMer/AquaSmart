from datetime import date
from django.core.mail import send_mail
from django.conf import settings

from cultures.models import Culture, NotificationLog
from users.models import UserProfile
from cultures.services_irrigation import (
    doit_etre_arrosee_aujourdhui,
    doit_etre_recoltee_aujourdhui,
)


def envoyer_notifications_cultures_pour_aujourdhui():
    today = date.today()
    cultures = Culture.objects.select_related("farm").all()

    # cultures à notifier aujourd'hui, regroupées par ferme
    notifications_par_ferme = {}

    for culture in cultures:
        farm = culture.farm
        if not farm:
            continue

        doit_arroser = doit_etre_arrosee_aujourdhui(culture, today)
        doit_recolter = doit_etre_recoltee_aujourdhui(culture, today)

        if not doit_arroser and not doit_recolter:
            continue

        # 🔴 Vérifier si cette culture a déjà été notifiée aujourd'hui
        deja_notifie = NotificationLog.objects.filter(
            farm=farm,
            culture=culture,
            date=today
        ).exists()

        if deja_notifie:
            continue  # on saute, déjà incluse dans un email précédent aujourd'hui

        # ✅ Sinon, on la ajoute à la liste à notifier
        if farm.id not in notifications_par_ferme:
            notifications_par_ferme[farm.id] = {
                "farm": farm,
                "cultures_arrosage": [],
                "cultures_recolte": [],
            }

        if doit_arroser:
            notifications_par_ferme[farm.id]["cultures_arrosage"].append(culture)

        if doit_recolter:
            notifications_par_ferme[farm.id]["cultures_recolte"].append(culture)

    # ------------------------
    #  ENVOI DES EMAILS
    # ------------------------
    for data in notifications_par_ferme.values():
        farm = data["farm"]
        cultures_arrosage = data["cultures_arrosage"]
        cultures_recolte = data["cultures_recolte"]

        membres = (
            UserProfile.objects
            .filter(farm=farm, is_active=True, user__is_active=True)
            .select_related("user")
        )

        destinataires = [m.user.email for m in membres if m.user.email]

        if not destinataires:
            owner_email = getattr(farm.owner, "email", None)
            if owner_email:
                destinataires = [owner_email]
            else:
                continue

        lignes = []

        if cultures_arrosage:
            lignes.append("🌧️ Nouvelles cultures à arroser aujourd'hui :")
            for c in cultures_arrosage:
                lignes.append(f"  - {c.nom} ({c.get_type_display()})")
            lignes.append("")

        if cultures_recolte:
            lignes.append("🌾 Nouvelles cultures à récolter aujourd'hui :")
            for c in cultures_recolte:
                lignes.append(f"  - {c.nom} ({c.get_type_display()})")

        corps = "\n".join(lignes)

        send_mail(
            f"[AquaSmart] Nouvelles actions à réaliser — {farm.name}",
            corps,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            destinataires,
            fail_silently=False,
        )

        # 🟢 Marquer chaque culture comme "notifiée aujourd'hui"
        for c in cultures_arrosage + cultures_recolte:
            NotificationLog.objects.get_or_create(
                farm=farm,
                culture=c,
                date=today,
            )

    return len(notifications_par_ferme)
