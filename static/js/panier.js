document.addEventListener("DOMContentLoaded", function () {
    const cartItemsContainer = document.getElementById("cart-items");
    const totalPriceElement = document.getElementById("total-price");
    const panierVideMessage = document.getElementById("panier-vide-message");
    const passerAuPaiementBtn = document.getElementById("passer-au-paiement");
  
    let panier = JSON.parse(localStorage.getItem("panier")) || [];
  
    function afficherPanier() {
      cartItemsContainer.innerHTML = "";
      let total = 0;
  
      if (panier.length === 0) {
        panierVideMessage.style.display = "block";
        passerAuPaiementBtn.disabled = true;
        return;
      }
  
      panierVideMessage.style.display = "none";
      passerAuPaiementBtn.disabled = false;
  
      panier.forEach((produit, index) => {
        const item = document.createElement("div");
        item.classList.add("border", "rounded", "p-3", "mb-2");
        item.innerHTML = `
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>${produit.nom}</strong> - ${produit.prix} TND<br>
              Quantité: ${produit.quantite}
            </div>
            <button class="btn btn-sm btn-danger" onclick="supprimerProduit(${index})">🗑 Supprimer</button>
          </div>
        `;
        cartItemsContainer.appendChild(item);
        total += produit.prix * produit.quantite;
      });
  
      total += 7; // frais de livraison
      totalPriceElement.textContent = `Total à payer : ${total.toFixed(2)} TND`;
    }
  
    window.supprimerProduit = function (index) {
      panier.splice(index, 1);
      localStorage.setItem("panier", JSON.stringify(panier));
      afficherPanier();
    };
  
    document.getElementById("order-form").addEventListener("submit", function (e) {
      e.preventDefault();
  
      if (panier.length === 0) {
        panierVideMessage.style.display = "block";
        return;
      }
  
      // Rediriger vers la page de paiement
      window.location.href = "paiment.html"; // change cette URL si besoin
    });
  
    afficherPanier();
  });
  