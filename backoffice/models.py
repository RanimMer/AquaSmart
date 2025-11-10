from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta


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
    sol = models.ForeignKey(
        'AnalyseSol',
        on_delete=models.PROTECT,          # empêche la suppression d’un sol utilisé
        related_name="cultures",
        null=True,                         # voir stratégie de migration plus bas
        blank=True,
        db_index=True
    )
    pin_surface = models.CharField(max_length=20, blank=True)  # Optionnel, pour stocker le type du sol

    def save(self, *args, **kwargs):
        if self.sol:
            self.pin_surface = self.sol.pin_surface  # Récupère le type du sol choisi
        super().save(*args, **kwargs)

    
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
class AnalyseSol(models.Model):
    TYPE_SOL_CHOICES = [
        ('argileux', 'Argileux'),
        ('sableux', 'Sableux'),
        ('limoneux', 'Limoneux'),
        ('humifere', 'Humifère'),
    ]
    
    # Attributs de base
    id_analyse = models.AutoField(primary_key=True)
    pin_surface = models.CharField(max_length=20, choices=TYPE_SOL_CHOICES, default='autre')
    date_analyse = models.DateField(auto_now_add=True)
    surface = models.DecimalField(max_digits=10, decimal_places=2, help_text="Surface en hectares")
    total_region = models.CharField(max_length=100, verbose_name="Région totale")
    bundles_composition = models.TextField(verbose_name="Composition des bundles")
    qualite_sol = models.CharField(max_length=50, choices=[
        ('excellente', 'Excellente'),
        ('bonne', 'Bonne'),
        ('moyenne', 'Moyenne'),
        ('mauvaise', 'Mauvaise'),
    ])
    
    
    # Paramètres chimiques du sol
    ph = models.DecimalField(max_digits=3, decimal_places=1)
    azote = models.DecimalField(max_digits=5, decimal_places=2, help_text="mg/kg")
    phosphore = models.DecimalField(max_digits=5, decimal_places=2, help_text="mg/kg")
    potassium = models.DecimalField(max_digits=5, decimal_places=2, help_text="mg/kg")
    
    # Localisation et recommandations
    localisation = models.CharField(max_length=200)
    recommandations = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Analyse de sol"
        verbose_name_plural = "Analyses de sol"
        ordering = ['-date_analyse']
    
    def __str__(self):
        return f"Analyse {self.id_analyse} - {self.pin_surface}"
    def get_photo_url(self):
        """Retourne l'URL complète de la photo du sol"""
        if self.photo_sol and hasattr(self.photo_sol, 'url'):
            return self.photo_sol.url
        return None
    def get_absolute_url(self):
        """URL pour accéder au détail de l'analyse"""
        return reverse('analyse_detail', kwargs={'pk': self.pk})
    
    # Méthodes (pour plus tard)
    def calculer_qualite(self):
        """Méthode pour calculer automatiquement la qualité du sol"""
        # À implémenter après le CRUD
        pass
    
    def generer_recommandations(self):
        """Méthode pour générer des recommandations automatiques"""
        # À implémenter après le CRUD
        pass
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

    sol = models.ForeignKey(
        'AnalyseSol',
        on_delete=models.PROTECT,          # empêche la suppression d’un sol utilisé
        related_name="Plantation",
        null=True,                         # voir stratégie de migration plus bas
        blank=True,
        db_index=True
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