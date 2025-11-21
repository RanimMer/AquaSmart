from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Farm

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Prénom", required=False)
    last_name  = forms.CharField(label="Nom", required=False)

    # Champs profil
    role  = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, label="Rôle")
    phone = forms.CharField(label="Téléphone", required=False)
    farm  = forms.ModelChoiceField(
        queryset=Farm.objects.all(),
        label="Ferme",
        required=False,
        help_text="Facultatif (tu peux l’assigner plus tard)."
    )
    is_active = forms.BooleanField(label="Actif", required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",
                  "role", "phone", "farm", "is_active")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name  = self.cleaned_data.get("last_name", "")
        user.is_active  = self.cleaned_data.get("is_active", True)

        if commit:
            user.save()
            # profil auto via signal, puis on met à jour
            profile = user.profile
            profile.role  = self.cleaned_data["role"]
            profile.phone = self.cleaned_data.get("phone", "")
            profile.farm  = self.cleaned_data.get("farm")
            profile.save()
        return user
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Prénom", required=False)
    last_name  = forms.CharField(label="Nom", required=False)
    is_active  = forms.BooleanField(label="Actif", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active")

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ( "role","phone", "farm", "avatar")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # récupérer l’utilisateur connecté
        super().__init__(*args, **kwargs)

        # Filtrer les fermes sur l'utilisateur connecté
        if user and not user.is_superuser:
            self.fields['farm'].queryset = Farm.objects.filter(owner=user)
        else:
            # admin = peut voir toutes les fermes
            self.fields['farm'].queryset = Farm.objects.all()

class FarmForm(forms.ModelForm):
        class Meta:
            model = Farm
            fields = ['name', 'location']
            widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom de la ferme"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Localisation"}),
            }

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Farm

class UserSignupForm(UserCreationForm):
    ROLE_CHOICES = [
        ("", "Sélectionnez votre type de compte"),
        ("ADMIN", "Agriculteur Propriétaire (Admin)"),
        ("TECH", "Employé Agricole"),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="Type de compte",
        help_text="Choisissez 'Agriculteur Propriétaire' si vous êtes le propriétaire de l'exploitation"
    )
    email = forms.EmailField(required=True)

    # 👇 nouveaux champs
    first_name = forms.CharField(label="Prénom", required=True)
    last_name  = forms.CharField(label="Nom", required=True)

    # champ ferme (pour employés)
    farm = forms.ModelChoiceField(
        queryset=Farm.objects.all(),
        required=False,
        label="Ferme / Exploitation",
        help_text="Sélectionnez la ferme à laquelle vous appartenez (si vous êtes employé)."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "farm",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control form-control-lg',
            })

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        farm = cleaned_data.get("farm")

        if role == "TECH" and not farm:
            self.add_error("farm", "Vous devez sélectionner la ferme à laquelle vous appartenez.")
        return cleaned_data

    def save(self, commit=True):
        """
        On complète le User avec email / prénom / nom.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")

        if commit:
            user.save()
        return user
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
class FrontUserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Prénom", required=False)
    last_name  = forms.CharField(label="Nom", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email


class FrontUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("phone", "farm", "avatar")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)   # utilisateur connecté (l’employé)
        super().__init__(*args, **kwargs)

        # On ne veut surtout pas que ce champ casse le form
        self.fields['farm'].required = False

        # On récupère le profil lié au form
        profile = self.instance or (getattr(user, "profile", None) if user else None)

        if profile and profile.farm:
            # 👉 une seule ferme : celle assignée à l’employé
            self.fields['farm'].queryset = Farm.objects.filter(pk=profile.farm_id)
            self.fields['farm'].initial = profile.farm
            self.fields['farm'].disabled = True  # il ne peut pas la changer
        else:
            self.fields['farm'].queryset = Farm.objects.none()

