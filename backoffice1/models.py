from django.db import models
# Create your models here.


class AnalyseSol(models.Model):
    TYPE_SOL_CHOICES = [
        ('argileux', 'Argileux'),
        ('sableux', 'Sableux'),
        ('limoneux', 'Limoneux'),
        ('humifere', 'Humifère'),
    ]
    
    # Attributs de base
    id_analyse = models.AutoField(primary_key=True)
    date_analyse = models.DateField(auto_now_add=True)
    pin_surface = models.CharField(max_length=50, verbose_name="PIN Surface")
    surface = models.DecimalField(max_digits=10, decimal_places=2, help_text="Surface en hectares")
    total_region = models.CharField(max_length=100, verbose_name="Région totale")
    bundles_composition = models.TextField(verbose_name="Composition des bundles")
    qualite_sol = models.CharField(max_length=50, choices=[
        ('excellente', 'Excellente'),
        ('bonne', 'Bonne'),
        ('moyenne', 'Moyenne'),
        ('mauvaise', 'Mauvaise'),
    ])
    photo_sol = models.ImageField(upload_to='photos_sols/', blank=True, null=True)
    
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
    
    # Méthodes (pour plus tard)
    def calculer_qualite(self):
        """Méthode pour calculer automatiquement la qualité du sol"""
        # À implémenter après le CRUD
        pass
    
    def generer_recommandations(self):
        """Méthode pour générer des recommandations automatiques"""
        # À implémenter après le CRUD
        pass