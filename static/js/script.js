/*produits*/
// Liste des nourritures (simulée)
const nourriture = [
    { id: 1, type: "Les matières grasses", nom: "Pâtes", prix: "2€", image: "img/Makarounie.jpeg" },
    { id: 2, type: "Les fruits et les légumes", nom: "Orange", prix: "3€", image: "img/orange.jpeg" },
    { id: 3, type: "La viande, le poisson et les fruits de mer", nom: "Poisson", prix: "20€", image: "img/poisson.jpeg" },
    { id: 4, type: "Les produits laitiers", nom: "Lait", prix: "1.2€", image: "img/lait.jpeg" },
];

// Fonction pour afficher les nourritures
function afficherNourriture(filtrenom = "", filtreType = "all") {
    const container = document.getElementById("nourritureContainer");
    container.innerHTML = ""; // Vide l'affichage actuel

    const resultats = nourriture.filter(item => {
        return (filtreType === "all" || item.type === filtreType) &&
               (filtrenom === "" || item.nom.toLowerCase().includes(filtrenom.toLowerCase()));
    });

    if (resultats.length === 0) {
        container.innerHTML = "<p>Aucune offre trouvée.</p>";
        return;
    }

    resultats.forEach(item => {
        let card = document.createElement("div");
        card.classList.add("nourriture-card");
        card.innerHTML = `
            <img src="${item.image}" alt="${item.type}">
            <h4>${item.nom} - ${item.type.charAt(0).toUpperCase() + item.type.slice(1)}</h4>
            <p>Prix : ${item.prix}</p>
        `;
        container.appendChild(card);
    });
}

// Gestion du formulaire de recherche
document.getElementById("searchForm").addEventListener("submit", function(event) {
    event.preventDefault();
    const nom = document.getElementById("searchInput").value;
    const typee = document.getElementById("categorySelect").value;
    afficherNourriture(nom, typee);
});



// Charger les nourritures au démarrage
afficherNourriture();
