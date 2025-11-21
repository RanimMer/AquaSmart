# produits/forms.py
from django import forms
from .models import Produit

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        # on n’affiche PAS le champ farm
        exclude = ['farm']
