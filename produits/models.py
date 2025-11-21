from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from django.conf import settings

from users.models import Farm  # ✅ AJOUT

from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

from users.models import Farm  # 🔗 pour lier au propriétaire (ferme)


class Produit(models.Model):
    # 🔗 Nouvelle logique : chaque produit appartient à une ferme
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="produits",
        null=True,
        blank=True,
    )

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
