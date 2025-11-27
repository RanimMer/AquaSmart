// Mise à jour du montant total
let total = panier.reduce((sum, article) => sum + article.prix * article.quantite, 0);
document.getElementById('montant_total_input').value = total.toFixed(2);
document.getElementById('montant_total_input_visible').value = total.toFixed(2) + " €";
