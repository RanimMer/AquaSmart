document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('order-form');
    let isProcessing = false;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (isProcessing) return;
        isProcessing = true;
        
        const submitBtn = document.getElementById('btn-passer-commande');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement...';

        try {
            // Validation des champs
            if (!validateForm()) {
                throw new Error('Veuillez corriger les erreurs du formulaire');
            }

            // Préparation des données
            const formData = {
                id_commande: document.getElementById('id_commande').value,
                date_commande: document.getElementById('date_commande').value,
                resume_articles: document.getElementById('resume_articles').value,
                montant_total: document.getElementById('montant_total_input').value,
                nom_client: document.getElementById('nom_client').value,
                prenom_client: document.getElementById('prenom_client').value,
                email_client: document.getElementById('email_client').value
            };

            // Envoi AJAX
            const response = await fetch('../../Controller/ajouter_commande.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || 'Erreur lors de l\'enregistrement');
            }

            // Succès - Vider le panier et rediriger
            localStorage.removeItem('panier');
            window.location.href = 'panier.php?success=1&id=' + result.commande_id;

        } catch (error) {
            console.error('Erreur:', error);
            // Afficher l'erreur dans l'interface
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i> ${error.message}`;
            form.appendChild(errorDiv);
            
            // Supprimer l'alerte après 5s
            setTimeout(() => errorDiv.remove(), 5000);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            isProcessing = false;
        }
    });

    function validateForm() {
        let isValid = true;
        
        // Validation des champs (ajoutez votre logique de validation ici)
        const nom = document.getElementById('nom_client');
        const prenom = document.getElementById('prenom_client');
        const email = document.getElementById('email_client');
        
        // Réinitialiser les erreurs
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.error-msg').forEach(el => el.remove());
        
        // Validation Nom
        if (!nom.value.trim()) {
            afficherErreur(nom, 'Le nom est obligatoire');
            isValid = false;
        }
        
        // Validation Prénom
        if (!prenom.value.trim()) {
            afficherErreur(prenom, 'Le prénom est obligatoire');
            isValid = false;
        }
        
        // Validation Email
        if (!email.value.trim()) {
            afficherErreur(email, 'L\'email est obligatoire');
            isValid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
            afficherErreur(email, 'Format email invalide');
            isValid = false;
        }
        
        return isValid;
    }
    
    function afficherErreur(input, message) {
        input.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-msg text-danger mt-1';
        errorDiv.textContent = message;
        input.parentNode.appendChild(errorDiv);
    }
});