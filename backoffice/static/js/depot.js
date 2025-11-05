function validateForm() {
    // Réinitialiser les messages d'erreur
    document.querySelectorAll('.error-message').forEach(function (element) {
        element.innerText = '';
    });

    let isValid = true;

    // Vérification du nom du dépôt
    const nomDepot = document.getElementById('nom_depot').value;
    const nomDepotRegex = /^[A-Z][a-zA-Z\s]*$/; // Commence par une majuscule, lettres et espaces
    if (nomDepot.trim() === '') {
        document.getElementById('nom_depot_error').innerText = 'Le nom du dépôt est vide .';
        isValid = false;
    } else if (!nomDepotRegex.test(nomDepot)) {
        document.getElementById('nom_depot_error').innerText = 'Le nom du dépôt doit commencer par une majuscule et contenir uniquement des lettres.';
        isValid = false;
    }

    // Vérification de l'adresse du dépôt
    const adresseDepot = document.getElementById('adresse_depot').value;
if (adresseDepot.trim() === '') {
    document.getElementById('adresse_depot_error').innerText = 'L\'adresse du dépôt est requise.';
    isValid = false;
} else if (!adresseDepot.includes('@') || !adresseDepot.endsWith('.com')) {
    document.getElementById('adresse_depot_error').innerText = 'L\'adresse doit contenir un "@" et se terminer par ".com".';
    isValid = false;
}


    // Vérification de la quantité maximale
    const quantiteMax = document.getElementById('quantite_max').value;
    if (quantiteMax.trim() === '') {
        document.getElementById('quantite_max_error').innerText = 'La quantité maximale est vide.';
        isValid = false;
    } else if (isNaN(quantiteMax) || Number(quantiteMax) <= 0) {
        document.getElementById('quantite_max_error').innerText = 'La quantité maximale doit être un nombre supérieur à zéro.';
        isValid = false;
    }

    return isValid; // Retourne true si tout est OK
}
