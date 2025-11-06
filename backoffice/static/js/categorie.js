function validateCategoryForm() {
    // Réinitialiser les messages d'erreur
    document.querySelectorAll('.error-message').forEach(function (element) {
        element.innerText = '';
    });

    let isValid = true;

    // Vérification du nom de la catégorie
    const nomCategorie = document.getElementById('nom_categorie').value;
    const nomCategorieRegex = /^[A-Z][a-zA-Z\s]*$/; // Commence par une majuscule et contient uniquement des lettres et des espaces
    if (nomCategorie.trim() === '') {
        document.getElementById('nom_categorie_error').innerText = 'Le nom de la catégorie est requis.';
        isValid = false;
    } else if (!nomCategorieRegex.test(nomCategorie)) {
        document.getElementById('nom_categorie_error').innerText = 'Le nom de la catégorie doit commencer par une majuscule.';
        isValid = false;
    }

    return isValid; // Retourne true si le formulaire est valide, sinon false
}