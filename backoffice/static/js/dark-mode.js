// Fonction pour initialiser le mode sombre
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return; // Sortir si le bouton n'existe pas
    
    const icon = darkModeToggle.querySelector('i');
    const html = document.documentElement;
    
    // Vérifier si le mode sombre est enregistré dans localStorage
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    
    // Appliquer le mode sombre si nécessaire
    if (isDarkMode) {
        html.setAttribute('data-theme', 'dark');
        if (icon) {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }
    
    // Gérer le clic sur le bouton de mode sombre
    darkModeToggle.addEventListener('click', function() {
        if (html.getAttribute('data-theme') === 'dark') {
            // Passer au mode clair
            html.setAttribute('data-theme', 'light');
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
            localStorage.setItem('darkMode', 'false');
        } else {
            // Passer au mode sombre
            html.setAttribute('data-theme', 'dark');
            if (icon) {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
            localStorage.setItem('darkMode', 'true');
        }
    });
}

// Appliquer le mode sombre au chargement de la page
function applyDarkModeOnLoad() {
    const html = document.documentElement;
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    
    if (isDarkMode) {
        html.setAttribute('data-theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
    }
}

// Appliquer immédiatement pour éviter le flash de contenu
applyDarkModeOnLoad();

// Initialiser le mode sombre une fois que le DOM est chargé
document.addEventListener('DOMContentLoaded', initDarkMode);