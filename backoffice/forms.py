from django import forms
from .models import Plantation

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
            'nombrePlantes': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control'
            }),
            'nomSerre': forms.TextInput(attrs={'class': 'form-control'}),
            'nomCulture': forms.TextInput(attrs={'class': 'form-control'}),
            'variete': forms.TextInput(attrs={'class': 'form-control'}),
            'etat': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des help_text
        self.fields['datesIrrigation'].help_text = "Une date par ligne (format: JJ/MM/AAAA)"
        self.fields['frequenceArrosage'].help_text = "Ex: Tous les 2 jours, 2 fois par semaine, etc."