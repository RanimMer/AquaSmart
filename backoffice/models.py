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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        # Vérifier que surface_m2 n'est pas None avant de comparer
        if self.surface_m2 is not None and self.surface_m2 <= 0:
            errors['surface_m2'] = "La surface doit être supérieure à 0."

        # Vérifier que besoin_base_l_j n'est pas None avant de comparer
        if self.besoin_base_l_j is not None and self.besoin_base_l_j < 0:
            errors['besoin_base_l_j'] = "Le besoin ne peut pas être négatif."

        # Vérifier que les dates ne sont pas None avant de comparer
        if (self.date_recolte_prevue is not None and 
            self.date_semis is not None and 
            self.date_recolte_prevue <= self.date_semis):
            errors['date_recolte_prevue'] = "La date de récolte doit être après la date de semis."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Appeler clean() avant la sauvegarde
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def age_jours(self):
        if self.date_semis:
            return (date.today() - self.date_semis).days
        return 0

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"