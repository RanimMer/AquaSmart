from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import date 

def upload_culture_image(instance, filename):
    return f"serres/{filename}"

class Plantation(models.Model):

    # Identifiant principal
    idSerre = models.AutoField(primary_key=True)

    # Nom de la serre avec valeur par défaut → pour éviter l'erreur
    nomSerre = models.CharField(
        max_length=100,
        default="Serre Principale",
        verbose_name="Nom de la serre"
    )

    # Informations de la plantation
    nomCulture = models.CharField(
        max_length=100,
        verbose_name="Nom de la culture"
    )

    variete = models.CharField(
        max_length=100,
        verbose_name="Variété"
    )

    # Nombre de plantes doit être ≥ 1
    nombrePlantes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de plantes"
    )

    # Dates
    dateSemis = models.DateField(
        verbose_name="Date de semis"
    )

    dateRecoltePrevue = models.DateField(
        verbose_name="Date de récolte prévue"
    )

    # États possibles
    etat = models.CharField(
        max_length=20,
        choices=[
            ('Semée', 'Semée'),
            ('Croissance', 'Croissance'),
            ('Floraison', 'Floraison'),
            ('Maturité', 'Maturité'),
            ('Récoltée', 'Récoltée'),
            ('Abîmée', 'Abîmée'),
        ],
        verbose_name="État actuel"
    )

    # Historique d'irrigations
    datesIrrigation = models.TextField(
        verbose_name="Dates d'irrigation (une date par ligne)",
        blank=True
    )

    # Fréquence choisie par l'agriculteur
    frequenceArrosage = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Fréquence d'arrosage"
    )

    # Mise à jour automatique
    dateDerniereMiseAJour = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )

    # Image de la plantation
    image = models.ImageField(
        upload_to=upload_culture_image,
        blank=True,
        null=True,
        verbose_name="Image de la plantation"
    )

    # Validation logique supplémentaire
    def clean(self):
        if self.dateRecoltePrevue and self.dateSemis:
            if self.dateRecoltePrevue < self.dateSemis:
                raise ValidationError("La date de récolte ne peut pas être avant la date de semis.")

    def __str__(self):
        return f"Serre {self.nomSerre} - {self.nomCulture} ({self.variete})"

    class Meta:
        verbose_name = "Plantation"
        verbose_name_plural = "Plantations"