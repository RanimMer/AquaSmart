<script>
document.addEventListener("DOMContentLoaded", function() {
    // Récupérer le formulaire et les champs
    const form = document.querySelector("form");
    const contenuField = document.getElementById("contenu_reponse");
    const idAdminField = document.getElementById("id_admin");
    
    // Créer des éléments pour afficher les messages d'erreur
    const contenuError = document.createElement("div");
    contenuError.className = "text-danger mt-1";
    contenuError.style.fontSize = "0.875rem";
    contenuField.parentNode.appendChild(contenuError);
    
    const idAdminError = document.createElement("div");
    idAdminError.className = "text-danger mt-1";
    idAdminError.style.fontSize = "0.875rem";
    idAdminField.parentNode.appendChild(idAdminError);
    
    // Fonction pour afficher un message d'erreur
    function showError(element, message) {
        element.textContent = message;
        element.style.display = "block";
    }
    
    // Fonction pour cacher un message d'erreur
    function hideError(element) {
        element.textContent = "";
        element.style.display = "none";
    }
    
    // Fonction pour vérifier si une chaîne contient uniquement des chiffres
    function containsOnlyDigits(str) {
        return /^\d+$/.test(str);
    }
    
    // Fonction pour vérifier si une chaîne contient uniquement des caractères spéciaux
    function containsOnlySpecialChars(str) {
        return /^[^a-zA-Z0-9]+$/.test(str);
    }
    
    // Fonction pour vérifier si une chaîne contient uniquement des caractères spéciaux et des chiffres
    function containsOnlySpecialCharsAndDigits(str) {
        return /^[^a-zA-Z]+$/.test(str);
    }
    
    // Fonction pour vérifier si une chaîne contient au moins une lettre
    function containsLetter(str) {
        return /[a-zA-Z]/.test(str);
    }
    
    // Validation du contenu de la réponse
    contenuField.addEventListener("input", function() {
        validateContenu();
    });
    
    function validateContenu() {
        const contenu = contenuField.value.trim();
        
        // Réinitialiser les styles
        contenuField.classList.remove("is-invalid", "is-valid");
        hideError(contenuError);
        
        // Vérifier si le contenu est vide
        if (contenu === "") {
            showError(contenuError, "Le contenu de la réponse est obligatoire.");
            contenuField.classList.add("is-invalid");
            return false;
        }
        
        // Vérifier la longueur minimale
        if (contenu.length < 5) {
            showError(contenuError, "Le contenu doit contenir au moins 5 caractères.");
            contenuField.classList.add("is-invalid");
            return false;
        }
        
        // Vérifier si le contenu contient uniquement des chiffres
        if (containsOnlyDigits(contenu)) {
            showError(contenuError, "Le contenu ne peut pas contenir uniquement des chiffres.");
            contenuField.classList.add("is-invalid");
            return false;
        }
        
        // Vérifier si le contenu contient uniquement des caractères spéciaux
        if (containsOnlySpecialChars(contenu)) {
            showError(contenuError, "Le contenu ne peut pas contenir uniquement des caractères spéciaux.");
            contenuField.classList.add("is-invalid");
            return false;
        }
        
        // Vérifier si le contenu contient uniquement des caractères spéciaux et des chiffres
        if (containsOnlySpecialCharsAndDigits(contenu)) {
            showError(contenuError, "Le contenu doit contenir au moins une lettre.");
            contenuField.classList.add("is-invalid");
            return false;
        }
        
        // Si toutes les validations sont passées
        contenuField.classList.add("is-valid");
        return true;
    }
    
    // Validation de l'ID admin
    idAdminField.addEventListener("input", function() {
        validateIdAdmin();
    });
    
    function validateIdAdmin() {
        const idAdmin = idAdminField.value.trim();
        
        // Réinitialiser les styles
        idAdminField.classList.remove("is-invalid", "is-valid");
        hideError(idAdminError);
        
        // Vérifier si l'ID admin est vide
        if (idAdmin === "") {
            showError(idAdminError, "L'ID admin est obligatoire.");
            idAdminField.classList.add("is-invalid");
            return false;
        }
        
        // Vérifier si l'ID admin contient exactement 8 chiffres
        if (!/^\d{8}$/.test(idAdmin)) {
            showError(idAdminError, "L'ID admin doit contenir exactement 8 chiffres.");
            idAdminField.classList.add("is-invalid");
            return false;
        }
        
        // Si toutes les validations sont passées
        idAdminField.classList.add("is-valid");
        return true;
    }
    
    // Validation du formulaire lors de la soumission
    form.addEventListener("submit", function(event) {
        // Valider tous les champs
        const isContenuValid = validateContenu();
        const isIdAdminValid = validateIdAdmin();
        
        // Si un champ n'est pas valide, empêcher la soumission du formulaire
        if (!isContenuValid || !isIdAdminValid) {
            event.preventDefault();
        }
    });
    
    // Ajouter des styles CSS pour les champs valides et invalides
    const style = document.createElement("style");
    style.textContent = `
        .is-invalid {
            border-color: #dc3545 !important;
            padding-right: calc(1.5em + 0.75rem) !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e") !important;
            background-repeat: no-repeat !important;
            background-position: right calc(0.375em + 0.1875rem) center !important;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
        }
        
        .is-valid {
            border-color: #198754 !important;
            padding-right: calc(1.5em + 0.75rem) !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%23198754' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e") !important;
            background-repeat: no-repeat !important;
            background-position: right calc(0.375em + 0.1875rem) center !important;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
        }
    `;
    document.head.appendChild(style);
});
</script>