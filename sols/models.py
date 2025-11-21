from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

from users.models import Farm  # ✅ AJOUT

from django.db import models
from users.models import Farm  # 🔗 lien avec la ferme


class AnalyseSol(models.Model):
    # 🔗 nouvelle logique : analyse liée à une ferme
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
    surface = models.DecimalField(max_digits=10, decimal_places=2, help_text="Surface en hectares")
    total_region = models.CharField(max_length=100, verbose_name="Région totale")
    bundles_composition = models.TextField(verbose_name="Composition des bundles")
    qualite_sol = models.CharField(max_length=50, choices=[
        ('excellente', 'Excellente'),
        ('bonne', 'Bonne'),
        ('moyenne', 'Moyenne'),
        ('mauvaise', 'Mauvaise'),
    ])
    
    ph = models.DecimalField(max_digits=3, decimal_places=1)
    azote = models.DecimalField(max_digits=5, decimal_places=2, help_text="mg/kg")
    phosphore = models.DecimalField(max_digits=5, decimal_places=2, help_text="mg/kg")
    potassium = models.DecimalField(max_digits=5, decimal_places=2, help_text="mg/kg")
    
    localisation = models.CharField(max_length=200)
    recommandations = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Analyse de sol"
        verbose_name_plural = "Analyses de sol"
        ordering = ['-date_analyse']
    
    def __str__(self):
        return f"Analyse {self.id_analyse} - {self.pin_surface}"
