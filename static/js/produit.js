function afficherNourriture(nom = "", type = "all") {
    let url = nom || type !== "all" ? `rechercher.php?nom=${nom}&type=${type}` : 'produit.php';

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("nourritureContainer");
            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = "<p>Aucune offre trouvée.</p>";
                return;
            }

            data.forEach(item => {
                let card = document.createElement("div");
                card.classList.add("nourriture-card");
                card.innerHTML = `
                    <img src="img/circus.png" alt="${item.type_produit}">
                    <h4>${item.nom_produit} - ${item.type_produit}</h4>
                    <p>Prix : ${item.prix_unitaire}€</p>
                `;
                container.appendChild(card);
            });
        });
}

document.getElementById("searchForm").addEventListener("submit", function(event) {
    event.preventDefault();
    const nom = document.getElementById("searchInput").value;
    const typee = document.getElementById("categorySelect").value;
    afficherNourriture(nom, typee);
});

window.addEventListener("DOMContentLoaded", () => {
    afficherNourriture();
});
