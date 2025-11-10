from django import forms
from .models import Produit, Culture, Plantation, AnalyseSol
from django.core.exceptions import ValidationError
from backoffice.models import AnalyseSol  # 🔹 modèle du module Sol

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = '__all__'


class CultureForm(forms.ModelForm):
    

    class Meta:
        model = Culture
        fields = ['nom', 'sol', 'type', 'surface_m2', 'date_semis', 'date_recolte_prevue', 'besoin_base_l_j', 'image']
        widgets = {
            'sol': forms.Select(attrs={'class': 'form-control'}),
            'date_semis': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_recolte_prevue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la culture'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'surface_m2': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0.01',
                'placeholder': 'Surface en m²'
            }),
            'besoin_base_l_j': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0',
                'placeholder': 'Besoin en eau (L/jour)'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

        # Rendre tous les champs obligatoires sauf image
        for field_name, field in self.fields.items():
            if field_name != 'image':
                field.required = True
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.sol:
            instance.pin_surface = instance.sol.pin_surface  # ✅ récupère le type de sol sélectionné
        if commit:
            instance.save()
        return instance

    # 🔹 Les validations restent inchangées
    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if not nom:
            raise ValidationError("Le nom est obligatoire.")
        if len(nom.strip()) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 caractères.")
        return nom.strip()

    def clean_surface_m2(self):
        surface_m2 = self.cleaned_data.get('surface_m2')
        if surface_m2 is None:
            raise ValidationError("La surface est obligatoire.")
        if surface_m2 <= 0:
            raise ValidationError("La surface doit être supérieure à 0.")
        if surface_m2 > 100000:
            raise ValidationError("La surface ne peut pas dépasser 100 000 m².")
        return surface_m2

    def clean_besoin_base_l_j(self):
        besoin = self.cleaned_data.get('besoin_base_l_j')
        if besoin is None:
            raise ValidationError("Le besoin en eau est obligatoire.")
        if besoin < 0:
            raise ValidationError("Le besoin en eau ne peut pas être négatif.")
        if besoin > 10000:
            raise ValidationError("Le besoin en eau est trop élevé.")
        return besoin

    def clean_date_semis(self):
        date_semis = self.cleaned_data.get('date_semis')
        if not date_semis:
            raise ValidationError("La date de semis est obligatoire.")
        return date_semis

    def clean_date_recolte_prevue(self):
        date_recolte_prevue = self.cleaned_data.get('date_recolte_prevue')
        if not date_recolte_prevue:
            raise ValidationError("La date de récolte prévue est obligatoire.")
        return date_recolte_prevue

    def clean(self):
        cleaned_data = super().clean()
        date_semis = cleaned_data.get('date_semis')
        date_recolte_prevue = cleaned_data.get('date_recolte_prevue')

        if date_semis and date_recolte_prevue:
            if date_recolte_prevue <= date_semis:
                self.add_error('date_recolte_prevue', "La date de récolte doit être après la date de semis.")
            
            from datetime import date, timedelta
            if date_semis > date.today() + timedelta(days=365):
                self.add_error('date_semis', "La date de semis ne peut pas être plus d'un an dans le futur.")

        image = cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            if image.size > 5 * 1024 * 1024:
                self.add_error('image', "L'image ne peut pas dépasser 5MB.")
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            extension = image.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                self.add_error('image', f"Format non supporté. Utilisez: {', '.join(valid_extensions)}")

        return cleaned_data


class PlantationForm(forms.ModelForm):
    class Meta:
        model = Plantation
        fields = '__all__'
        widgets = {
            'dateSemis': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dateRecoltePrevue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'datesIrrigation': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control',
                'placeholder': 'Entrez une date par ligne (format: JJ/MM/AAAA)'
            }),
            'frequenceArrosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Tous les 2 jours'
            }),
            'heureArrosage': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control'
            }),
            'nombrePlantes': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control'
            }),
            'nomSerre': forms.TextInput(attrs={'class': 'form-control'}),
            'nomCulture': forms.TextInput(attrs={'class': 'form-control'}),
            'variete': forms.TextInput(attrs={'class': 'form-control'}),
            'etat': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'sol': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['datesIrrigation'].help_text = "Une date par ligne (format: JJ/MM/AAAA)"
        self.fields['frequenceArrosage'].help_text = "Ex: Tous les 2 jours, 2 fois par semaine, etc."
        self.fields['heureArrosage'].help_text = "Heure fixe pour l'arrosage (ex: 08:00)"
