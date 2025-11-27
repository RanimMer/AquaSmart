document.addEventListener('DOMContentLoaded', function() {
    // Initialiser la date minimum
    const dateInput = document.getElementById('date_livraison');
    if (dateInput) {
        const today = new Date();
        const minDate = new Date(today);
        minDate.setDate(today.getDate() + 2);
        dateInput.min = minDate.toISOString().split('T')[0];
    }

    // Fonctions de validation
    function validateAdresse() {
        const value = document.getElementById('adresse').value.trim();
        const errorElement = document.getElementById('adresseError');
        
        if (!value) {
            errorElement.textContent = "L'adresse est obligatoire";
            return false;
        }
        errorElement.textContent = '';
        return true;
    }

    function validateVille() {
        const value = document.getElementById('ville').value.trim();
        const errorElement = document.getElementById('villeError');
        
        if (!value) {
            errorElement.textContent = "La ville est obligatoire";
            return false;
        }
        errorElement.textContent = '';
        return true;
    }

    function validateCodePostal() {
        const value = document.getElementById('code_postal').value.trim();
        const errorElement = document.getElementById('codePostalError');
        
        if (!value) {
            errorElement.textContent = "Le code postal est obligatoire";
            return false;
        }
        if (!/^\d{4}$/.test(value)) {
            errorElement.textContent = "Le code postal doit contenir 4 chiffres";
            return false;
        }
        errorElement.textContent = '';
        return true;
    }

    function validateDate() {
        const value = document.getElementById('date_livraison').value;
        const errorElement = document.getElementById('dateError');
        
        if (!value) {
            errorElement.textContent = "La date est obligatoire";
            return false;
        }
        
        const today = new Date();
        const minDate = new Date(today);
        minDate.setDate(today.getDate() + 2);
        const selectedDate = new Date(value);
        
        if (selectedDate <= minDate) {
            const formattedDate = minDate.toLocaleDateString('fr-FR');
            errorElement.textContent = `La date doit être après le ${formattedDate}`;
            return false;
        }
        
        errorElement.textContent = '';
        return true;
    }

    // Validation en temps réel
    document.getElementById('adresse').addEventListener('blur', validateAdresse);
    document.getElementById('ville').addEventListener('blur', validateVille);
    document.getElementById('code_postal').addEventListener('blur', validateCodePostal);
    document.getElementById('date_livraison').addEventListener('change', validateDate);

    // Gestion de la soumission du formulaire
    const livraisonForm = document.getElementById('livraisonForm');
    if (livraisonForm) {
        livraisonForm.addEventListener('submit', function(e) {
            // Valider tous les champs avant soumission
            const isAdresseValid = validateAdresse();
            const isVilleValid = validateVille();
            const isCodePostalValid = validateCodePostal();
            const isDateValid = validateDate();
            
            if (!isAdresseValid || !isVilleValid || !isCodePostalValid || !isDateValid) {
                e.preventDefault();
                const firstError = document.querySelector('.text-danger:not(:empty)');
                if (firstError) {
                    firstError.closest('.delivery-field').scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            }
        });
    }
});