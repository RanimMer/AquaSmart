from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test , permission_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth import login , authenticate
from .forms import UserCreateForm, UserUpdateForm, UserProfileForm , UserSignupForm
from django.contrib.auth.forms import UserCreationForm
from django.utils.decorators import method_decorator
from .models import Farm, UserProfile
from .forms import FarmForm 
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Case, When, Value, IntegerField, Q
from .forms import FrontUserUpdateForm, FrontUserProfileForm




# --- Petit décorateur simple pour restreindre au "vrai" admin du projet
# --- Admin / propriétaire ou superuser ---
def is_admin_or_superuser(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    prof = getattr(user, "profile", None)
    return bool(prof and prof.role == "ADMIN")


admin_required = user_passes_test(is_admin_or_superuser, login_url="login")


@login_required
@admin_required
def users_list(request):
    me = request.user

    # Les fermes de l’admin connecté
    my_farms = Farm.objects.filter(owner=me)

    # Tous les comptes visibles pour cet admin :
    # - lui-même
    # - ses employés (rattachés à ses fermes)
    qs = (
        User.objects.select_related("profile")
        .filter(Q(pk=me.pk) | Q(profile__farm__in=my_farms))
        .exclude(is_superuser=True)
        .distinct()
        # --- clé de tri : l'admin connecté en 1er, puis le reste
        .annotate(
            sort_owner=Case(
                When(pk=me.pk, then=Value(0)),  # l'admin loggé en tout premier
                default=Value(1),
                output_field=IntegerField(),
            ),
            # (optionnel) met les autres admins après toi mais avant les TECH
            sort_role=Case(
                When(profile__role="ADMIN", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
        .order_by("sort_owner", "sort_role", "username")
    )

    return render(request, "backoffice/users/users_list.html", {"users": qs})


@login_required
@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur “{user.username}” créé avec succès.")
            return redirect("users_list")
    else:
        form = UserCreateForm()
    return render(request, "backoffice/users/users_form.html", {
        "form_user": form,
        "form_profile": None,  # on n’en a pas besoin à la création (déjà dans form_user)
        "title": "Créer un utilisateur",
        "submit_label": "Créer",
    })

@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = user.profile  # existe via signal

    if request.method == "POST":
        form_user = UserUpdateForm(request.POST, instance=user)
        form_profile = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            form_profile.save()
            messages.success(request, f"Utilisateur “{user.username}” mis à jour.")
            return redirect("users_list")
    else:
        form_user = UserUpdateForm(instance=user)
        form_profile = UserProfileForm(instance=profile)

    return render(request, "backoffice/users/users_form.html", {
        "form_user": form_user,
        "form_profile": form_profile,
        "title": f"Éditer l’utilisateur : {user.username}",
        "submit_label": "Enregistrer",
    })

@login_required
@admin_required
def user_delete(request, user_id):
    """
    Suppression d’un utilisateur depuis le backoffice.

    - Si on supprime un employé -> on supprime juste l'utilisateur.
    - Si on supprime un ADMIN propriétaire :
        -> on supprime aussi ses fermes
        -> on supprime ses employés rattachés à ces fermes
    - Si l’admin supprime SON propre compte :
        -> idem + logout + redirection vers login.
    """

    user_to_delete = get_object_or_404(User, pk=user_id)
    is_self = (user_to_delete == request.user)

    if request.method == "POST":
        username = user_to_delete.username
        profile = getattr(user_to_delete, "profile", None)

        # 1) Si c'est un admin propriétaire → nettoyer ses fermes + employés
        if profile and profile.role == "ADMIN":
            # Toutes ses fermes
            farms = Farm.objects.filter(owner=user_to_delete)

            # Tous les employés liés à ces fermes (sauf lui-même)
            User.objects.filter(
                profile__farm__in=farms,
                is_superuser=False
            ).exclude(pk=user_to_delete.pk).delete()
            # Les fermes sauteront automatiquement via on_delete=CASCADE
            # (Farm.owner → User)

        # 2) Si c’est lui-même → déconnexion AVANT suppression
        if is_self:
            logout(request)

        # 3) Suppression du compte (admin ou employé)
        user_to_delete.delete()

        # 4) Redirection
        if is_self:
            messages.success(
                request,
                "Votre compte et toutes les données associées ont été supprimés."
            )
            return redirect("login")
        else:
            messages.success(request, f"Utilisateur « {username} » supprimé.")
            return redirect("users_list")

    # GET -> page de confirmation
    return render(
        request,
        "backoffice/users/users_confirm_delete.html",
        {"user_obj": user_to_delete},
    )



@login_required
def profile_view(request):
    """Edition du profil de l'utilisateur connecté (admin ou employé)."""
    user = request.user
    # Profil garanti par le signal ; sinon on le crée au vol
    profile = getattr(user, "profile", None)
    if profile is None:
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        form_user = UserUpdateForm(request.POST, instance=user)
        form_profile = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            form_profile.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("profile_view")
    else:
        form_user = UserUpdateForm(instance=user)
        form_profile = UserProfileForm(instance=profile, user=request.user)

    return render(request, "backoffice/users/my_profile.html", {
        "form_user": form_user,
        "form_profile": form_profile,
        "title": "Mon profil",
        "submit_label": "Enregistrer",
    })

#@login_required
#def profile_view(request):
    #return profile_view(request)

@login_required
def profile_edit(request):
    return profile_view(request)

# LIST
@login_required
@admin_required
def farm_list(request):
    if request.user.is_superuser:
        # superuser voit tout
        farms = Farm.objects.all().order_by('name')
    else:
        # chaque admin ne voit que ses propres fermes
        farms = Farm.objects.filter(owner=request.user).order_by('name')

    return render(request, 'backoffice/farms/list.html', {'farms': farms})


# CREATE
@login_required
@admin_required
def farm_create(request):
    if request.method == 'POST':
        form = FarmForm(request.POST)
        if form.is_valid():
            farm = form.save(commit=False)
            farm.owner = request.user   # <-- IMPORTANT
            farm.save()
            messages.success(request, "Ferme créée avec succès.")
            return redirect('farm_list')
    else:
        form = FarmForm()
    return render(request, 'backoffice/farms/form.html', {'form': form, "submit_label": "Créer"})

# EDIT
@login_required
@admin_required
def farm_update(request, pk):
    if request.user.is_superuser:
        farm = get_object_or_404(Farm, pk=pk)
    else:
        # l’admin ne peut modifier que ses propres fermes
        farm = get_object_or_404(Farm, pk=pk, owner=request.user)

    if request.method == "POST":
        form = FarmForm(request.POST, instance=farm)
        if form.is_valid():
            form.save()
            messages.success(request, "Ferme mise à jour.")
            return redirect("farm_list")
    else:
        form = FarmForm(instance=farm)

    return render(request, "backoffice/farms/form.html", {"form": form, "submit_label": "Mettre à jour"})


# DELETE
@login_required
@admin_required
def farm_delete(request, pk):
    if request.user.is_superuser:
        farm = get_object_or_404(Farm, pk=pk)
    else:
        # l’admin ne peut supprimer que ses fermes
        farm = get_object_or_404(Farm, pk=pk, owner=request.user)

    if request.method == 'POST':
        farm.delete()
        messages.success(request, "Ferme supprimée.")
        return redirect('farm_list')

    return render(request, 'backoffice/farms/confirm_delete.html', {'farm': farm})


def signup(request):
    """Inscription avec choix du rôle"""
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = form.cleaned_data['role']

            if profile.role == "ADMIN":
                # 🔹 L’admin crée automatiquement sa ferme
                user.is_staff = True
                user.save()

                farm_count = Farm.objects.count() + 1
                farm = Farm.objects.create(
                    owner=user,
                    name=f"Ferme{farm_count}",
                )

                profile.farm = farm

            elif profile.role == "TECH":
                # 🔹 L’employé choisit la ferme à laquelle il appartient
                farm_id = request.POST.get("farm")
                if farm_id:
                    try:
                        profile.farm = Farm.objects.get(pk=farm_id)
                    except Farm.DoesNotExist:
                        profile.farm = None

            profile.save()

            # 🔐 Connexion automatique après inscription
            login(request, user)
            messages.success(request, f"Compte {profile.get_role_display()} créé avec succès !")

            # 🔀 Redirection selon le rôle
            if profile.role == "ADMIN":
                return redirect('bo_dashboard')  # Backoffice admin
            else:
                return redirect('index')          # Frontoffice employé

    else:
        form = UserSignupForm()

    # 🧠 Envoi de toutes les fermes au template
    farms = Farm.objects.all()
    return render(request, 'registration/signup.html', {'form': form, 'farms': farms})


# Vue de connexion personnalisée pour la redirection
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        storage = messages.get_messages(self.request)
        for _ in storage:
            pass
        # Redirection selon le rôle après connexion
        user = self.request.user
        if user.is_superuser or hasattr(user, 'profile') and user.profile.role == "ADMIN":
            return reverse('bo_dashboard')  # Backoffice pour admin
        else:
            return reverse('index')  # Frontoffice pour employés
        

def index(request):
    """Page d'accueil"""
    return render(request, 'public/index.html')

def apropos(request):
    """Page À propos"""
    return render(request, 'public/apropos.html')

def contact(request):
    """Page Contact"""
    return render(request, 'public/contact.html')

from .forms import (
    FrontUserUpdateForm,
    FrontUserProfileForm,
    # (et tes autres forms backoffice si besoin)
)

@login_required
def front_profile_view(request):
    """Profil côté FRONT (employé)."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        form_user = FrontUserUpdateForm(request.POST, instance=user)
        form_profile = FrontUserProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user,   # ⚠️ important
        )

        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()

            profil_obj = form_profile.save(commit=False)

            # Sécurité : on garde la ferme d’origine de l’employé
            if profile.farm:
                profil_obj.farm = profile.farm

            profil_obj.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("index")   # /profil/
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form_user = FrontUserUpdateForm(instance=user)
        form_profile = FrontUserProfileForm(
            instance=profile,
            user=request.user,
        )

    return render(request, "public/profile_front.html", {
        "form_user": form_user,
        "form_profile": form_profile,
    })
