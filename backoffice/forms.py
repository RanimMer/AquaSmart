from .models import Culture
from django import forms
from backoffice.models import Culture
from django.core.exceptions import ValidationError

class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ['nom', 'type', 'surface_m2', 'date_semis', 'date_recolte_prevue', 'besoin_base_l_j', 'image']
        widgets = {
            'date_semis': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_recolte_prevue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.required = True
            existing = f.widget.attrs.get('class', '')
            f.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean(self):
        cleaned = super().clean()
        semis = cleaned.get('date_semis')
        recolte = cleaned.get('date_recolte_prevue')

        if semis and recolte and recolte <= semis:
            self.add_error('date_recolte_prevue', "La date de récolte doit être après la date de semis.")

        return cleaned
