from django.db import models
from users.models import Farm

class AnalyseSol(models.Model):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="analyses_sol",
        null=True,
        blank=True,
    )

    TYPE_SOL_CHOICES = [
        ('argileux', 'Argileux'),
        ('sableux', 'Sableux'),
        ('limoneux', 'Limoneux'),
        ('humifere', 'Humifère'),
    ]
    
    id_analyse = models.AutoField(primary_key=True)
    pin_surface = models.CharField(max_length=20, choices=TYPE_SOL_CHOICES, default='argileux')
    date_analyse = models.DateField(auto_now_add=True)
    surface = models.DecimalField(max_digits=10, decimal_places=2)
    total_region = models.CharField(max_length=100)
    bundles_composition = models.TextField()
    
    # Champ calculé
    qualite_sol = models.CharField(max_length=50, editable=False)
    
    ph = models.DecimalField(max_digits=3, decimal_places=1)
    azote = models.DecimalField(max_digits=5, decimal_places=2)
    phosphore = models.DecimalField(max_digits=5, decimal_places=2)
    potassium = models.DecimalField(max_digits=5, decimal_places=2)
    
    localisation = models.CharField(max_length=200)
    recommandations = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Analyse de sol"
        verbose_name_plural = "Analyses de sol"
        ordering = ['-date_analyse']
    
    def __str__(self):
        return f"Analyse {self.id_analyse} - {self.pin_surface}"

    def save(self, *args, **kwargs):
        # Calcul automatique de la qualité
        self.qualite_sol = self.calculer_qualite()
        
        # Génération automatique de recommandations selon la qualité
        if self.qualite_sol == 'excellente':
            self.recommandations = "Le sol est en excellente condition. Maintenir les pratiques actuelles."
        elif self.qualite_sol == 'bonne':
            self.recommandations = "Le sol est en bonne condition. Ajouter éventuellement du compost ou de l'engrais équilibré."
        elif self.qualite_sol == 'moyenne':
            self.recommandations = "Le sol est moyen. Ajouter du compost et fertiliser régulièrement pour améliorer la qualité."
        else:  # mauvaise
            self.recommandations = "Le sol est pauvre. Amendement intensif nécessaire : compost, engrais et correction du pH."

        super().save(*args, **kwargs)

    def calculer_qualite(self):
        score = 0

        # Poids simples pour chaque paramètre
        if 6.0 <= self.ph <= 7.5:
            score += 2
        elif 5.5 <= self.ph < 6.0 or 7.5 < self.ph <= 8.0:
            score += 1

        if self.azote >= 20:
            score += 2
        elif 10 <= self.azote < 20:
            score += 1

        if self.phosphore >= 15:
            score += 2
        elif 7 <= self.phosphore < 15:
            score += 1

        if self.potassium >= 150:
            score += 2
        elif 80 <= self.potassium < 150:
            score += 1

        # Définition de la qualité selon le score
        if score >= 7:
            return 'excellente'
        elif score >= 5:
            return 'bonne'
        elif score >= 3:
            return 'moyenne'
        else:
            return 'mauvaise'

    @property
    def recommandations_auto(self):
        """Retourne des recommandations même si le champ 'recommandations' est vide."""
        if self.qualite_sol == 'excellente':
            return "Le sol est en excellente condition. Maintenir les pratiques actuelles."
        elif self.qualite_sol == 'bonne':
            return "Le sol est en bonne condition. Ajouter éventuellement du compost ou de l'engrais équilibré."
        elif self.qualite_sol == 'moyenne':
            return "Le sol est moyen. Ajouter du compost et fertiliser régulièrement pour améliorer la qualité."
        else:
            return "Le sol est pauvre. Amendement intensif nécessaire : compost, engrais et correction du pH."
    def anomalies(self):
        erreurs = []

        # Exemple de seuils critiques (à ajuster)
        if self.ph < 4 or self.ph > 9:
            erreurs.append("pH très anormal : intervention urgente nécessaire.")

        if self.azote < 5:
            erreurs.append("Azote extrêmement faible.")

        if self.phosphore < 2:
            erreurs.append("Phosphore critique.")

        if self.potassium < 2:
            erreurs.append("Potassium critique.")

        # Exemple : surface incohérente
        if self.surface <= 0:
            erreurs.append("Surface invalide.")

        return erreurs

    def est_critique(self):
        return len(self.anomalies()) > 0
