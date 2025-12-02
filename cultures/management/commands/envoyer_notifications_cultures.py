from datetime import date

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from cultures.models import Culture
from users.models import UserProfile
from cultures.services_irrigation import (
    doit_etre_arrosee_aujourdhui,
    doit_etre_recoltee_aujourdhui,
)


class Command(BaseCommand):
    help = (
        "Envoie des notifications par email aux petits agriculteurs (TECH) "
        "pour les cultures à arroser ou à récolter aujourd'hui."
    )

    def handle(self, *args, **options):
        aujourd_hui = date.today()

        cultures = Culture.objects.select_related("farm").all()

        notifications_par_ferme = {}

        for culture in cultures:
            farm = culture.farm
            if not farm:
                continue

            doit_arroser = doit_etre_arrosee_aujourdhui(culture, aujourd_hui)
            doit_recolter = doit_etre_recoltee_aujourdhui(culture, aujourd_hui)

            if not doit_arroser and not doit_recolter:
                continue

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

        for data in notifications_par_ferme.values():
            farm = data["farm"]
            cultures_arrosage = data["cultures_arrosage"]
            cultures_recolte = data["cultures_recolte"]

            # 🔹 petits agriculteurs TECH de cette ferme
            membres = (
                UserProfile.objects
                .select_related("user")
                .filter(
                    farm=farm,
                    role="TECH",
                    is_active=True,
                    user__is_active=True,
                )
            )

            destinataires = [
                m.user.email
                for m in membres
                if m.user.email
            ]

            # fallback possible sur le propriétaire, si tu veux
            if not destinataires:
                owner_email = getattr(farm.owner, "email", None)
                if owner_email:
                    destinataires = [owner_email]
                else:
                    continue

            sujet = f"[AquaSmart] Cultures à gérer – {farm.name} – {aujourd_hui.strftime('%d/%m/%Y')}"

            lignes = []

            if cultures_arrosage:
                lignes.append("🌧️ Cultures à arroser aujourd'hui :")
                for c in cultures_arrosage:
                    lignes.append(
                        f"  - {c.nom} ({c.get_type_display()}) | besoin: {c.besoin_base_l_j} L/j | semis: {c.date_semis}"
                    )
                lignes.append("")

            if cultures_recolte:
                lignes.append("🌾 Cultures à récolter aujourd'hui :")
                for c in cultures_recolte:
                    lignes.append(
                        f"  - {c.nom} ({c.get_type_display()}) | récolte prévue: {c.date_recolte_prevue}"
                    )
                lignes.append("")

            corps = "\n".join(lignes) if lignes else "Aucune action requise aujourd'hui."

            self.stdout.write(self.style.SUCCESS(
                f"Envoi d'un email à {', '.join(destinataires)} pour la ferme {farm.name}"
            ))
            self.stdout.write(corps)
            self.stdout.write("-" * 60)

            send_mail(
                sujet,
                corps,
                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@aquasmart.local"),
                destinataires,
                fail_silently=False,
            )
