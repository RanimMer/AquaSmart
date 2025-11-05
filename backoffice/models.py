from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import date

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

    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autre')

    surface_m2 = models.DecimalField(max_digits=10, decimal_places=2, help_text="Surface en m²")

    date_semis = models.DateField()
    date_recolte_prevue = models.DateField()

    besoin_base_l_j = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Besoin en eau (litres/jour)"
    )

    image = models.ImageField(
        upload_to=upload_culture_image,
        null=True, blank=True
    )

    """
    # Clés étrangères
    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cultures'
    )

    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.PROTECT,
        related_name='cultures'
    )

    serre = models.ForeignKey(
        'serres.Serre',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cultures'
    )
    """
    # Dates automatiques
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------- CONTRÔLE DE SAISIE -------
    def clean(self):
        errors = {}

        if self.surface_m2 <= 0:
            errors['surface_m2'] = "La surface doit être supérieure à 0."

        if self.besoin_base_l_j < 0:
            errors['besoin_base_l_j'] = "Le besoin ne peut pas être négatif."

        if self.date_recolte_prevue and self.date_recolte_prevue <= self.date_semis:
            errors['date_recolte_prevue'] = "La date de récolte doit être après la date de semis."

        if errors:
            raise ValidationError(errors)

    # ------- GETTER SIMPLE (pas de setter) -------
    @property
    def age_jours(self):
        return (date.today() - self.date_semis).days

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
