from django.shortcuts import render
from backoffice.models import Produit
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.genai import Client, types
import re

client = Client(api_key="AIzaSyDm2w2KcxDE1Jie3Sulf-7sRr172z45pEw")

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

@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        try:
            question = request.POST.get("question", "")
            image = request.FILES.get("image")

            if not question and not image:
                return JsonResponse({"error": "Aucune donnée reçue"}, status=400)

            parts = []

            # Si question texte existe, l'ajouter comme part
            if question:
                parts.append(types.Part.from_text(text=question))

            # Si image existe, l'ajouter comme part
            if image:
                image_bytes = image.read()
                parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image.content_type))

            # Créer un content “user” avec ces parts
            content = types.Content(
                role="user",
                parts=parts
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",  # ou un modèle Gemini approprié
                contents=[content],
                config=types.GenerateContentConfig(temperature=0.7)
            )

            answer = response.text
            # Optionnel : nettoyer la réponse
            answer = re.sub(r'(\*\*|\*)', '', answer)

            return JsonResponse({"answer": answer})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

