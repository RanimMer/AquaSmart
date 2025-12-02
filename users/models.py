from django.conf import settings
from django.db import models

class Farm(models.Model):
    owner = models.ForeignKey(  # agriculteur principal (ou admin “propriétaire”)
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_farms"
    )
    name = models.CharField("Nom de la ferme", max_length=150)
    location = models.CharField("Localisation", max_length=255, blank=True)
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ferme"
        verbose_name_plural = "Fermes"

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Agriculteur propriétaire"),  # propriétaire 
        ("TECH",  "Employé agricole"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    role = models.CharField("Rôle", max_length=10, choices=ROLE_CHOICES, default="TECH")

    # 🔗 Nouveau : rattacher l’utilisateur à une ferme (optionnel pour le moment)
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")

    avatar = models.ImageField("Avatar", upload_to="avatars/", blank=True, null=True)
    is_active = models.BooleanField("Actif", default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Profil de {self.user.get_username()}"
