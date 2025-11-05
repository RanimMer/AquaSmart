function validateForm() {
    // Réinitialiser les messages d'erreur
    document.querySelectorAll('.error-message').forEach(function(element) {
        element.textContent = '';
    });
    document.querySelectorAll('.form-control').forEach(el => el.classList.remove('is-invalid'));

    let isValid = true;

    // Fonction utilitaire pour afficher les erreurs
    function showError(fieldId, message) {
        document.getElementById(`${fieldId}_error`).textContent = message;
        document.getElementById(fieldId).classList.add('is-invalid');
        isValid = false;
    }

    // Validation du nom de la recette
    const nomRecette = document.getElementById('nom_recette').value.trim();
    if (nomRecette === '') {
        showError('nom_recette', 'Le nom de la recette est requis.');
    } else if (nomRecette.length > 250) {
        showError('nom_recette', 'Le nom ne doit pas dépasser 250 caractères.');
    }

    // Validation du temps de préparation (format HH:MM:SS)
    const tempsPreparation = document.getElementById('temps_preparation').value.trim();
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$/;
    if (tempsPreparation === '') {
        showError('temps_preparation', 'Le temps de préparation est requis.');
    } else if (!timeRegex.test(tempsPreparation)) {
        showError('temps_preparation', 'Format invalide. Utilisez HH:MM:SS.');
    }

    // Validation des ingrédients
    const ingredients = document.getElementById('ingredients').value.trim();
    if (ingredients === '') {
        showError('ingredients', 'Les ingrédients sont requis.');
    } else if (ingredients.length > 250) {
        showError('ingredients', 'Les ingrédients ne doivent pas dépasser 250 caractères.');
    }

    // Validation des instructions
    const instructions = document.getElementById('instructions').value.trim();
    if (instructions === '') {
        showError('instructions', 'Les instructions sont requises.');
    } else if (instructions.length > 250) {
        showError('instructions', 'Les instructions ne doivent pas dépasser 250 caractères.');
    }

    // Validation du type de recette
    const typeRecette = document.getElementById('type_recette').value;
    if (typeRecette === '') {
        showError('type_recette', 'Veuillez sélectionner un type de recette.');
    }

    // Validation de l'image
    const imageInput = document.getElementById('image_upload');
    const oldImage = document.querySelector('input[name="old_image"]')?.value;
    
    // Si nouvelle recette ou modification avec nouvelle image
    if (!oldImage && (!imageInput.files || imageInput.files.length === 0)) {
        showError('image_upload', 'Veuillez sélectionner une image.');
    } else if (imageInput.files.length > 0) {
        const file = imageInput.files[0];
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        const maxSize = 2 * 1024 * 1024; // 2MB
        
        if (!validTypes.includes(file.type)) {
            showError('image_upload', 'Seuls les formats JPG, PNG et GIF sont acceptés.');
        } else if (file.size > maxSize) {
            showError('image_upload', 'L\'image ne doit pas dépasser 2MB.');
        }
    }

    return isValid;
}

// Prévisualisation de l'image
function previewImage(event) {
    const preview = document.getElementById('image_preview');
    const file = event.target.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
}

// Écouteurs d'événements
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('formRecette');
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault(); // Bloquer l'envoi normal
            
            if (!validateForm()) return; // Afficher les erreurs si validation échoue

            // Soumission AJAX pour éviter le rechargement
            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    window.location.href = '../View/backoffice/recette.php?success=1';
                } else {
                    throw new Error('Erreur serveur');
                }
            } catch (error) {
                console.error('Erreur:', error);
                document.getElementById('form-error').textContent = 
                    'Une erreur est survenue. Veuillez réessayer.';
            }
        });
    }
});