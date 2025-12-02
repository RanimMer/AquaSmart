// Fichier JavaScript pour la gestion du paiement
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM entièrement chargé")
  
    // Récupérer les éléments du DOM
    const form = document.getElementById("paymentForm")
    const cardPayment = document.getElementById("cardPayment")
    const cashPayment = document.getElementById("cashPayment")
    const creditCardDetails = document.getElementById("creditCardDetails")
    const recapDiv = document.getElementById("paymentRecap")
  
    // Gestion des méthodes de paiement
    document.querySelectorAll('input[name="paymentMethod"]').forEach((radio) => {
      radio.addEventListener("change", function () {
        if (this.value === "carte") {
          cardPayment.classList.add("selected")
          cashPayment.classList.remove("selected")
          creditCardDetails.style.display = "block"
        } else {
          cardPayment.classList.remove("selected")
          cashPayment.classList.add("selected")
          creditCardDetails.style.display = "none"
  
          // Réinitialiser les validations pour les champs de carte
          document.querySelectorAll("#creditCardDetails input").forEach((input) => {
            input.classList.remove("is-invalid")
          })
        }
      })
    })
  
    // Initialiser l'affichage en fonction de la méthode sélectionnée par défaut
    const defaultMethod = document.querySelector('input[name="paymentMethod"]:checked')
    if (defaultMethod) {
      if (defaultMethod.value === "carte") {
        creditCardDetails.style.display = "block"
        cardPayment.classList.add("selected")
        cashPayment.classList.remove("selected")
      } else {
        creditCardDetails.style.display = "none"
        cardPayment.classList.remove("selected")
        cashPayment.classList.add("selected")
      }
    }
  
    // Validation du formulaire
    form.addEventListener("submit", (e) => {
      e.preventDefault()
  
      // Validation basique
      let isValid = true
      const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value
  
      if (paymentMethod === "carte") {
        // Validation des champs de carte uniquement si ce mode est sélectionné
        const cardNumber = document.getElementById("cardNumber")
        const cardName = document.getElementById("cardName")
        const cardExpiry = document.getElementById("cardExpiry")
        const cardCvv = document.getElementById("cardCvv")
  
        // Réinitialiser les validations
        ;[cardNumber, cardName, cardExpiry, cardCvv].forEach((field) => {
          field.classList.remove("is-invalid")
        })
  
        if (!/^\d{16}$/.test(cardNumber.value.replace(/\s/g, ""))) {
          cardNumber.classList.add("is-invalid")
          isValid = false
        }
  
        if (!/^[A-Za-z\s]+$/.test(cardName.value.trim())) {
          cardName.classList.add("is-invalid")
          isValid = false
        }
  
        if (!/^\d{2}\/\d{2}$/.test(cardExpiry.value.trim())) {
          cardExpiry.classList.add("is-invalid")
          isValid = false
        }
  
        if (!/^\d{3}$/.test(cardCvv.value.trim())) {
          cardCvv.classList.add("is-invalid")
          isValid = false
        }
      }
  
      if (isValid) {
        // Afficher un indicateur de chargement
        const submitBtn = form.querySelector('button[type="submit"]')
        const originalBtnText = submitBtn.innerHTML
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Traitement en cours...'
        submitBtn.disabled = true
  
        // Soumettre le formulaire via AJAX
        const formData = new FormData(form)
  
        // Déboguer les données envoyées
        console.log("Envoi des données au serveur:")
        for (const pair of formData.entries()) {
          console.log(pair[0] + ": " + pair[1])
        }
  
        fetch(form.action, {
          method: "POST",
          body: formData,
        })
          .then((response) => {
            // Vérifier si la réponse est OK
            if (!response.ok) {
              throw new Error("Erreur réseau: " + response.status)
            }
  
            // Essayer de parser le JSON
            return response.text().then((text) => {
              try {
                console.log("Réponse brute:", text)
                return JSON.parse(text)
              } catch (e) {
                console.error("Réponse non-JSON:", text)
                throw new Error("La réponse du serveur n'est pas au format JSON valide")
              }
            })
          })
          .then((data) => {
            console.log("Données reçues:", data)
            if (data.success) {
              // Afficher le récapitulatif
              recapDiv.style.display = "block"
              document.getElementById("recapMethod").textContent = data.method
              document.getElementById("recapDate").textContent = data.date
              document.getElementById("recapStatus").textContent = data.status
  
              // Masquer le formulaire
              document.querySelector(".payment-methods").style.display = "none"
  
              // Ajouter un bouton pour retourner à l'accueil
              const homeButton = document.createElement("a")
              homeButton.href = "index.html"
              homeButton.className = "btn btn-primary mt-3"
              homeButton.innerHTML = '<i class="fas fa-home mr-2"></i> Retour à l\'accueil'
              recapDiv.appendChild(homeButton)
  
              // Vider le panier
              localStorage.removeItem("panier")
              const cartCount = document.getElementById("cartCount")
              if (cartCount) {
                cartCount.textContent = "0"
              }
  
              // Faire défiler jusqu'au récapitulatif
              recapDiv.scrollIntoView({ behavior: "smooth" })
            } else {
              alert("Erreur: " + (data.error || "Une erreur est survenue"))
              // Restaurer le bouton
              submitBtn.innerHTML = originalBtnText
              submitBtn.disabled = false
            }
          })
          .catch((error) => {
            console.error("Erreur:", error)
            alert("Une erreur est survenue lors du traitement de votre paiement: " + error.message)
            // Restaurer le bouton
            submitBtn.innerHTML = originalBtnText
            submitBtn.disabled = false
          })
      }
    })
  })
  