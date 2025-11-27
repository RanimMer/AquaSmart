from .models import StationMeteo
from django.core.exceptions import ValidationError
from django import forms



class StationMeteoForm(forms.ModelForm):
    class Meta:
        model = StationMeteo
        fields = [
            'nom_station',
            'emplacement',
            'actif',
            'id_sol',
            'id_capteur_pluie',
            'id_capteur_luminosite_humidite',
            'id_capteur_vent',
            'sol',
            # (ne PAS inclure 'farm' ici)
        ]
        widgets = {
            'nom_station': forms.TextInput(attrs={'placeholder': 'Nom de la station'}),
            'emplacement': forms.TextInput(attrs={'placeholder': 'Emplacement de la station'}),
            'id_sol': forms.TextInput(attrs={'placeholder': 'ID capteur sol'}),
            'id_capteur_pluie': forms.TextInput(attrs={'placeholder': 'ID capteur pluie'}),
            'id_capteur_luminosite_humidite': forms.TextInput(attrs={'placeholder': 'ID capteur luminosité/humidité'}),
            'id_capteur_vent': forms.TextInput(attrs={'placeholder': 'ID capteur vent'}),
            'sol': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # cacher 'farm' si Django l’ajoute malgré tout
        if 'farm' in self.fields:
            self.fields.pop('farm')
