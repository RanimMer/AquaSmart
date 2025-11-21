from django.db import models
from django.core.exceptions import ValidationError
from datetime import date

from users.models import Farm  # 🔗 ferme propriétaire


def upload_culture_image(instance, filename):
    return f"cultures/{filename}"


class Culture(models.Model):
    TYPE_CHOICES = [
        ('legume', 'Légume'),
        ('fruit', 'Fruit'),
        ('cereale', 'Céréale'),
        ('aromatique', 'Plante Aromatique'),
        ('autre', 'Autre'),
    ]

    # 🔗 nouvelle logique : culture rattachée à une ferme
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="cultures",
        null=True,
        blank=True,
    )

    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autre')
    surface_m2 = models.DecimalField(max_digits=10, decimal_places=2, help_text="Surface en m²")
    date_semis = models.DateField()
    date_recolte_prevue = models.DateField()
    besoin_base_l_j = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Besoin en eau (litres/jour)"
    )
    image = models.ImageField(upload_to=upload_culture_image, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 🔗 Même logique que ton ancien code, mais relié via noms d'apps
    produits_utilises = models.ManyToManyField(
        'produits.Produit',          # 🔥 référence au modèle Produit de l’app "produits"
        through='CultureProduit',
        related_name='cultures'
    )

    sol = models.ForeignKey(
        'sols.AnalyseSol',           # 🔥 référence au modèle AnalyseSol de l’app "sols"
        on_delete=models.CASCADE,
        related_name="cultures",
        null=True,
        blank=True,
        db_index=True
    )

    pin_surface = models.CharField(max_length=20, blank=True)  # type du sol, comme tu avais

    def clean(self):
        errors = {}

        if self.surface_m2 is not None and self.surface_m2 <= 0:
            errors['surface_m2'] = "La surface doit être supérieure à 0."

        if self.besoin_base_l_j is not None and self.besoin_base_l_j < 0:
            errors['besoin_base_l_j'] = "Le besoin ne peut pas être négatif."

        if (
            self.date_recolte_prevue is not None
            and self.date_semis is not None
            and self.date_recolte_prevue <= self.date_semis
        ):
            errors['date_recolte_prevue'] = "La date de récolte doit être après la date de semis."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # ✅ garde ta logique de validation + pin_surface
        self.full_clean()

        if self.sol:
            self.pin_surface = self.sol.pin_surface

        super().save(*args, **kwargs)

    @property
    def age_jours(self):
        if self.date_semis:
            return (date.today() - self.date_semis).days
        return 0

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"


class CultureProduit(models.Model):
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE)
    produit = models.ForeignKey('produits.Produit', on_delete=models.CASCADE)
    quantite_utilisee = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.culture.nom} - {self.produit.nom_produit}"
