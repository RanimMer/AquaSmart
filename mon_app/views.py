from django.shortcuts import render
from backoffice.models import Produit
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.genai import Client, types
import re

# Initialise le client avec la clé API
client = Client(api_key="AIzaSyDm2w2KcxDE1Jie3Sulf-7sRr172z45pEw")  # ou utilisez GOOGLE_API_KEY

# Pages principales
def index(request):
    return render(request, 'index.html')

def produits(request):
    produits = Produit.objects.all()
    return render(request, 'produits.html', {'produits': produits})

def logout_view(request):
    return render(request, 'logout.html')

def apropos(request):
    return render(request, 'apropos.html')

def contact(request):
    return render(request, 'contact.html')

def chatbot_ia(request):
    return render(request, "chatbot_ia.html")

# API du chatbot (désactivé CSRF pour le développement)
@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question", "")
            if not question:
                return JsonResponse({"error": "Aucune question fournie"}, status=400)

            # Appel à Gemini via generate_content
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # ou un modèle Gemini valide
                contents=question,
                config=types.GenerateContentConfig(temperature=0.7)
            )

            answer = response.text
            answer = re.sub(r'(\*\*|\*)', '', answer)
            return JsonResponse({"answer": answer})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

