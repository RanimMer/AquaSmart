function validateForm() {
    // Réinitialiser les messages d'erreur
    document.querySelectorAll('.error-message').forEach(function (element) {
        element.innerText = '';
    });

    let isValid = true;

    // Vérification du nom du produit
    const nomProduit = document.getElementById('nom_produit').value;
    const nomProduitRegex = /^[A-Z][a-zA-Z0-9\s]*$/;
    if (nomProduit.trim() === '') {
        document.getElementById('nom_produit_error').innerText = 'Le nom du produit est requis.';
        isValid = false;
    } else if (!nomProduitRegex.test(nomProduit)) {
        document.getElementById('nom_produit_error').innerText = 'Le nom du produit doit commencer par une majuscule et ne contenir que des lettres, chiffres ou espaces.';
        isValid = false;
    }

    // Vérification du type de produit
    const typeProduit = document.getElementById('type_produit').value;
    if (typeProduit.trim() === '') {
        document.getElementById('type_produit_error').innerText = 'Le type de produit est requis.';
        isValid = false;
    }

    // Vérification du stock disponible
    const stockDisponible = document.getElementById('stock_disponible').value;
    if (stockDisponible.trim() === '') {
        document.getElementById('stock_disponible_error').innerText = 'Le stock disponible est requis.';
        isValid = false;
    } else if (isNaN(stockDisponible) || parseInt(stockDisponible) < 0) {
        document.getElementById('stock_disponible_error').innerText = 'Le stock doit être un nombre entier positif.';
        isValid = false;
    }

    // Vérification du prix unitaire
    const prixUnitaire = document.getElementById('prix_unitaire').value;
    if (prixUnitaire.trim() === '') {
        document.getElementById('prix_unitaire_error').innerText = 'Le prix unitaire est requis.';
        isValid = false;
    } else if (isNaN(prixUnitaire) || parseFloat(prixUnitaire) <= 0) {
        document.getElementById('prix_unitaire_error').innerText = 'Le prix doit être un nombre positif.';
        isValid = false;
    }

    // Vérification de l'image du produit
    const imageProduit = document.getElementById('image_produit');
    const imageProduitError = document.getElementById('image_produit_error');
    
    // Si c'est une nouvelle création, l'image est obligatoire
    if (document.querySelector('input[name="id_produit"]').value === '' && imageProduit.files.length === 0) {
        imageProduitError.innerText = 'L\'image du produit est requise.';
        isValid = false;
    } 
    // Si une image est sélectionnée, vérifier son type
    else if (imageProduit.files.length > 0) {
        const file = imageProduit.files[0];
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            imageProduitError.innerText = 'Le fichier doit être une image (JPEG, PNG ou GIF).';
            isValid = false;
        }
        
        // Vérifier la taille du fichier (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            imageProduitError.innerText = 'L\'image ne doit pas dépasser 2MB.';
            isValid = false;
        }
    }

    // Vérification du dépôt
    const depot = document.getElementById('depot').value;
    if (depot.trim() === '') {
        document.getElementById('depot_error').innerText = 'Le champ dépôt est requis.';
        isValid = false;
    }

    return isValid;
}

// Afficher un aperçu de l'image avant upload
document.getElementById('image_produit').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            let preview = document.getElementById('image-preview');
            if (!preview) {
                preview = document.createElement('img');
                preview.id = 'image-preview';
                preview.style.maxWidth = '200px';
                preview.style.maxHeight = '200px';
                preview.style.marginTop = '10px';
                e.target.parentNode.appendChild(preview);
            }
            preview.src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
});