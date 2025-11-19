from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

class Produit(models.Model):
    nom_produit = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(2, "Le nom du produit doit contenir au moins 2 caractères.")
        ]
    )

    type_produit = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-zÀ-ÿ\s-]+$',
                message="Le type de produit ne doit contenir que des lettres et des espaces."
            )
        ]
    )

    description = models.TextField(
        validators=[
            MinLengthValidator(10, "La description doit contenir au moins 10 caractères.")
        ]
    )

    quantite_stock = models.CharField(
    max_length=50,
    validators=[
        RegexValidator(
            # Commence par un ou plusieurs chiffres, puis optionnellement des lettres ou espaces
            regex=r'^[0-9]+[A-Za-zÀ-ÿ\s]*$',
            message="La quantité doit commencer par un nombre, suivi éventuellement d'unités (ex: '25 kg', '10 L')."
        )
    ]
)


    date_ajout = models.DateField(auto_now_add=True)

    image = models.ImageField(
    upload_to='produits/',
    blank=False,
    null=False
)

    def __str__(self):
        return self.nom_produit
