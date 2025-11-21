from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
import re
from users.models import Farm  # + ferme

class StationMeteo(models.Model):
    
    
    id_station = models.CharField(
        "ID Station", 
        max_length=4, 
        primary_key=True,
        unique=True,
        editable=False,  # Rendre non éditable
        help_text="Format: 0001, 0002, etc. Généré automatiquement"
    )

    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="stations_meteo",
        null=True,
        blank=True,
    )


    nom_station = models.CharField(
        "Nom de la station", 
        max_length=30
    )
    id_sol = models.CharField(
        "ID Capteur Sol", 
        max_length=50, 
        blank=True
    )
    id_capteur_pluie = models.CharField(
        "ID Capteur Pluie", 
        max_length=50, 
        blank=True
    )
    id_capteur_luminosite_humidite = models.CharField(
        "ID Capteur Luminosité/Humidité", 
        max_length=50, 
        blank=True
    )
    id_capteur_vent = models.CharField(
        "ID Capteur Vent", 
        max_length=50, 
        blank=True
    )
    date_installation = models.DateTimeField(
        "Date d'installation", 
        auto_now_add=True
    )
    emplacement = models.CharField(
        "Emplacement", 
        max_length=100, 
        blank=True
    )
    actif = models.BooleanField(
        "Station active", 
        default=True
    )
    ETAT_CHOICES = [
        ('connecte', 'Connecté'),
        ('deconnecte', 'Déconnecté'),]
    
    sol = models.ForeignKey(
        'sols.AnalyseSol',
        on_delete=models.CASCADE,
        related_name="stations_meteo",
        null=True,
        blank=True,
        db_index=True
    )


    def save(self, *args, **kwargs):
        if self.sol:
            self.pin_surface = self.sol.pin_surface  # Récupère le type du sol choisi
        super().save(*args, **kwargs)

    def clean(self):
        """Validation des données avant sauvegarde"""
        errors = {}
        
        # Validation Nom Station (obligatoire)
        if not self.nom_station or len(self.nom_station.strip()) < 2:
            errors['nom_station'] = "Le nom de la station est obligatoire et doit contenir au moins 2 caractères"
        elif len(self.nom_station) > 10:
            errors['nom_station'] = "Le nom de la station ne peut pas dépasser 10 caractères"
        elif not re.match(r'^[a-zA-Z0-9À-ÿ\s\-_\.]+$', self.nom_station):
            errors['nom_station'] = "Le nom contient des caractères non autorisés. Utilisez seulement des lettres, chiffres, espaces, -, _ et ."
        
        # Validation IDs capteurs (format général)
        capteurs = {
            'id_sol': self.id_sol,
            'id_capteur_pluie': self.id_capteur_pluie,
            'id_capteur_luminosite_humidite': self.id_capteur_luminosite_humidite,
            'id_capteur_vent': self.id_capteur_vent
        }
        
        for champ, valeur in capteurs.items():
            if valeur and not re.match(r'^[a-zA-Z0-9\-_\.]+$', valeur):
                errors[champ] = f"L'ID {champ} contient des caractères non autorisés. Utilisez seulement lettres, chiffres, -, _ et ."
        
        # Validation Emplacement
        if self.emplacement and len(self.emplacement.strip()) > 0:
            if len(self.emplacement) > 100:
                errors['emplacement'] = "L'emplacement ne peut pas dépasser 100 caractères"
            elif not re.match(r'^[a-zA-Z0-9À-ÿ\s\-\'\,\.]+$', self.emplacement):
                errors['emplacement'] = "L'emplacement contient des caractères non autorisés"
        
        # Lever toutes les erreurs ensemble
        if errors:
            raise ValidationError(errors)

    def _generer_id_auto(self):
        """Génère automatiquement le prochain ID station"""
        try:
            # Récupérer le dernier ID existant
            dernier_station = StationMeteo.objects.all().order_by('id_station').last()
            
            if not dernier_station:
                return "0001"  # Première station
            
            try:
                # Convertir l'ID en entier et incrémenter
                dernier_id_int = int(dernier_station.id_station)
                nouveau_id_int = dernier_id_int + 1
                
                # Vérifier la limite (0001 à 9999)
                if nouveau_id_int > 9999:
                    raise ValidationError("Nombre maximum de stations atteint (9999). Impossible de créer une nouvelle station.")
                
                return f"{nouveau_id_int:04d}"
                
            except ValueError:
                # En cas d'ID non numérique, utiliser le count + 1
                count = StationMeteo.objects.count()
                nouveau_id_int = count + 1
                if nouveau_id_int > 9999:
                    raise ValidationError("Nombre maximum de stations atteint (9999). Impossible de créer une nouvelle station.")
                return f"{nouveau_id_int:04d}"
                
        except Exception as e:
            # Fallback: utiliser le count + 1
            count = StationMeteo.objects.count()
            nouveau_id_int = count + 1
            if nouveau_id_int > 9999:
                raise ValidationError("Nombre maximum de stations atteint (9999). Impossible de créer une nouvelle station.")
            return f"{nouveau_id_int:04d}"

    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique de l'ID station"""
        
        # Générer ID station seulement pour les nouveaux objets
        if not self.id_station:
            self.id_station = self._generer_id_auto()
        
        # Nettoyer les données avant sauvegarde
        self._nettoyer_donnees()
        
        # Validation complète avant sauvegarde
        self.full_clean()
        
        super().save(*args, **kwargs)

    def _nettoyer_donnees(self):
        """Nettoie et formate les données avant sauvegarde"""
        # Nettoyer le nom de la station
        if self.nom_station:
            self.nom_station = self.nom_station.strip()
            # Capitaliser la première lettre de chaque mot
            self.nom_station = ' '.join(word.capitalize() for word in self.nom_station.split())
        
        # Nettoyer l'emplacement
        if self.emplacement:
            self.emplacement = self.emplacement.strip()
        
        # Nettoyer les IDs capteurs
        for champ in ['id_sol', 'id_capteur_pluie', 'id_capteur_luminosite_humidite', 'id_capteur_vent']:
            valeur = getattr(self, champ)
            if valeur:
                setattr(self, champ, valeur.strip().upper())  # Convertir en majuscules

    def __str__(self):
        status = "Active" if self.actif else "Inactive"
        return f"{self.id_station} - {self.nom_station} ({status})"

    class Meta:
        verbose_name = "Station Météo"
        verbose_name_plural = "Stations Météo"
        ordering = ['id_station']

    # Méthodes utilitaires
    @classmethod
    def get_prochain_id_disponible(cls):
        """Retourne le prochain ID station disponible"""
        instance = cls()
        return instance._generer_id_auto()
    
    @classmethod
    def verifier_limite_stations(cls):
        """Vérifie si la limite de 9999 stations est atteinte"""
        return cls.objects.count() >= 9999
    
    @classmethod
    def get_nombre_stations_actives(cls):
        """Retourne le nombre de stations actives"""
        return cls.objects.filter(actif=True).count()


