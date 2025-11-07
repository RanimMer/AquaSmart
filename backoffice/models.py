from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

class Produit(models.Model):
    nom_produit = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2, "Le nom du produit doit contenir au moins 2 caractères.")]
    )

    type_produit = models.CharField(
        max_length=50,
        validators=[RegexValidator(
            regex=r'^[A-Za-zÀ-ÿ\s-]+$',
            message="Le type de produit ne doit contenir que des lettres et des espaces."
        )]
    )

    description = models.TextField(
        validators=[MinLengthValidator(10, "La description doit contenir au moins 10 caractères.")]
    )

    quantite_stock = models.CharField(
        max_length=50,
        validators=[RegexValidator(
            regex=r'^[0-9]+[A-Za-zÀ-ÿ\s]*$',
            message="La quantité doit commencer par un nombre, suivi éventuellement d'unités (ex: '25 kg', '10 L')."
        )]
    )

    date_ajout = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='produits/', blank=False, null=False)

    def __str__(self):
        return self.nom_produit


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
    besoin_base_l_j = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Besoin en eau (litres/jour)")
    image = models.ImageField(upload_to=upload_culture_image, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    produits_utilises = models.ManyToManyField(
        'Produit',
        through='CultureProduit',
        related_name='cultures'
    )

    def clean(self):
        errors = {}

        if self.surface_m2 is not None and self.surface_m2 <= 0:
            errors['surface_m2'] = "La surface doit être supérieure à 0."

        if self.besoin_base_l_j is not None and self.besoin_base_l_j < 0:
            errors['besoin_base_l_j'] = "Le besoin ne peut pas être négatif."

        if (self.date_recolte_prevue is not None and 
            self.date_semis is not None and 
            self.date_recolte_prevue <= self.date_semis):
            errors['date_recolte_prevue'] = "La date de récolte doit être après la date de semis."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def age_jours(self):
        if self.date_semis:
            return (date.today() - self.date_semis).days
        return 0

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"


# ✅ Classe intermédiaire : table de liaison entre Culture et Produit
class CultureProduit(models.Model):
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_utilisee = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.culture.nom} - {self.produit.nom_produit}"
