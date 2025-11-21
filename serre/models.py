from django.db import models
from users.models import Farm  # +++ AJOUT
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
import re

def upload_culture_image(instance, filename):
    return f"serres/{filename}"

# Validateur personnalisé pour les noms (lettres, espaces et tirets)
nom_validator = RegexValidator(
    regex=r'^[a-zA-ZÀ-ÿ\s\-]+$',
    message='Le nom ne peut contenir que des lettres, espaces et tirets'
)

# Validateur pour les fréquences d'arrosage
frequence_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9\s\-]+$',
    message='La fréquence ne peut contenir que des lettres, chiffres, espaces et tirets'
)


class Plantation(models.Model):

    # Identifiant principal
    idSerre = models.AutoField(primary_key=True)

    # +++ AJOUT
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="plantations",
        null=True,
        blank=True,
    )

    
    # Nom de la serre avec valeur par défaut et validation
    nomSerre = models.CharField(
        max_length=100,
        default="Serre Principale",
        verbose_name="Nom de la serre",
        validators=[nom_validator],
        help_text="Nom de la serre (lettres, espaces et tirets uniquement)"
    )

    # Informations de la plantation avec validation
    nomCulture = models.CharField(
        max_length=100,
        verbose_name="Nom de la culture",
        validators=[nom_validator],
        help_text="Nom de la culture (ex: Tomate, Laitue, Carotte)"
    )

    variete = models.CharField(
        max_length=100,
        verbose_name="Variété",
        validators=[nom_validator],
        help_text="Variété spécifique (ex: Cerise, Romaine, Nantaise)"
    )

    # Nombre de plantes avec validation étendue
    nombrePlantes = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1, message="Le nombre de plantes doit être au moins 1"),
            MaxValueValidator(10000, message="Le nombre de plantes ne peut pas dépasser 10 000")
        ],
        verbose_name="Nombre de plantes",
        help_text="Nombre de plantes (entre 1 et 10 000)"
    )

    # Dates avec validation
    dateSemis = models.DateField(
        verbose_name="Date de semis",
        help_text="Date à laquelle les graines ont été semées"
    )

    dateRecoltePrevue = models.DateField(
        verbose_name="Date de récolte prévue",
        help_text="Date estimée de la récolte"
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
        verbose_name="État actuel",
        default='Semée'
    )

    # Historique d'irrigations avec validation
    datesIrrigation = models.TextField(
        verbose_name="Dates d'irrigation (une date par ligne)",
        blank=True,
        help_text="Entrez une date par ligne au format JJ/MM/AAAA"
    )

    # Fréquence d'arrosage avec validation
    frequenceArrosage = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Fréquence d'arrosage",
        validators=[frequence_validator],
        help_text="Ex: Tous les 2 jours, 3 fois par semaine, etc."
    )

    # NOUVEAU: Heure fixe d'arrosage
    heureArrosage = models.TimeField(
        verbose_name="Heure d'arrosage",
        blank=True,
        null=True,
        help_text="Heure fixe pour l'arrosage (ex: 08:00)",
        default='08:00'
    )

    # Mise à jour automatique
    dateDerniereMiseAJour = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )

    # Image de la plantation avec validation de taille
    image = models.ImageField(
        upload_to=upload_culture_image,
        blank=True,
        null=True,
        verbose_name="Image de la plantation",
        help_text="Format supporté: JPG, PNG, GIF. Taille max: 5MB"
    )

    # APRÈS  ✅ (référence qualifiée avec l'app-label)
    sol = models.ForeignKey(
        'sols.AnalyseSol',
        on_delete=models.CASCADE,
        related_name="Plantation",
        null=True, blank=True, db_index=True
    )
    

    def save(self, *args, **kwargs):
        if self.sol:
            self.pin_surface = self.sol.pin_surface  # Récupère le type du sol choisi
        super().save(*args, **kwargs)

    # ✅ VALIDATIONS AVANCÉES
    def clean(self):
        errors = {}
        
        # Validation 1: Date de récolte après date de semis
        if self.dateRecoltePrevue and self.dateSemis:
            if self.dateRecoltePrevue < self.dateSemis:
                errors['dateRecoltePrevue'] = "La date de récolte ne peut pas être avant la date de semis."
            
            # Validation 2: Date de semis dans le futur (max 1 an)
            if self.dateSemis > timezone.now().date() + timedelta(days=365):
                errors['dateSemis'] = "La date de semis ne peut pas être dans plus d'un an."
            
            # Validation 3: Date de récolte pas trop éloignée (max 2 ans)
            if self.dateRecoltePrevue > timezone.now().date() + timedelta(days=730):
                errors['dateRecoltePrevue'] = "La date de récolte ne peut pas être dans plus de 2 ans."
        
        # Validation 4: Dates d'irrigation format
        if self.datesIrrigation:
            dates_list = self.datesIrrigation.strip().split('\n')
            for i, date_str in enumerate(dates_list, 1):
                date_str = date_str.strip()
                if date_str:
                    try:
                        # Vérifier le format date
                        day, month, year = map(int, date_str.split('/'))
                        date(year, month, day)
                    except (ValueError, TypeError):
                        errors['datesIrrigation'] = f"Ligne {i}: Format de date invalide. Utilisez JJ/MM/AAAA"
        
        # Validation 5: Nombre de plantes selon l'état
        if self.etat == 'Récoltée' and self.nombrePlantes > 0:
            errors['nombrePlantes'] = "Une plantation récoltée doit avoir 0 plantes."
        
        # Si des erreurs, on les lève
        if errors:
            raise ValidationError(errors)

    # Méthode pour calculer la durée de croissance
    def duree_croissance(self):
        if self.dateSemis and self.dateRecoltePrevue:
            return (self.dateRecoltePrevue - self.dateSemis).days
        return None

    # Méthode pour vérifier si besoin d'arrosage
    def besoin_arrosage(self):
        if not self.datesIrrigation:
            return True
        
        dates_list = self.datesIrrigation.strip().split('\n')
        if dates_list:
            derniere_irrigation = dates_list[-1].strip()
            try:
                day, month, year = map(int, derniere_irrigation.split('/'))
                derniere_date = date(year, month, day)
                jours_ecoules = (timezone.now().date() - derniere_date).days
                
                # Si fréquence spécifiée, l'utiliser pour déterminer
                if 'jour' in self.frequenceArrosage.lower():
                    try:
                        frequence = int(''.join(filter(str.isdigit, self.frequenceArrosage)))
                        return jours_ecoules >= frequence
                    except:
                        pass
                
                # Sinon, par défaut tous les 3 jours
                return jours_ecoules >= 3
            except:
                pass
        return True

    def __str__(self):
        return f"Serre {self.nomSerre} - {self.nomCulture} ({self.variete})"

    class Meta:
        verbose_name = "Plantation"
        verbose_name_plural = "Plantations"
        ordering = ['-dateDerniereMiseAJour']