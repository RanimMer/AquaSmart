import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

# 📁 chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "plant_health_mobilenet.keras")
CLASSES_PATH = os.path.join(MODELS_DIR, "plant_health_classes.txt")

IMG_SIZE = (224, 224)

_model = None
_class_names = None


def _load_artifacts():
    """Charge le modèle et la liste des classes une seule fois."""
    global _model, _class_names

    if _model is None:
        print(f"🔄 Chargement du modèle depuis {MODEL_PATH}...")
        _model = load_model(MODEL_PATH)   # la couche Rescaling est DÉJÀ dedans

    if _class_names is None:
        print(f"🔄 Chargement des classes depuis {CLASSES_PATH}...")
        with open(CLASSES_PATH, "r", encoding="utf-8") as f:
            _class_names = [line.strip() for line in f if line.strip()]
        print("✅ Classes :", _class_names)


def predict_plant_health(image_path: str):
    """
    Retourne (label, confidence) pour une image donnée.
    label ∈ {'healthy', 'dry', 'yellow'} selon ton fichier de classes.
    """
    _load_artifacts()

    # 1) Charger et redimensionner l'image
    img = tf.keras.utils.load_img(image_path, target_size=IMG_SIZE)
    img_array = tf.keras.utils.img_to_array(img)   # [0..255]
    img_array = np.expand_dims(img_array, axis=0)  # shape (1, 224, 224, 3)

    # ⚠️ PAS de preprocess_input ici ! (Rescaling déjà dans le modèle)
    # 2) Prédiction
    preds = _model.predict(img_array)[0]  # ex: [0.1, 0.7, 0.2]
    idx = int(np.argmax(preds))
    confidence = float(preds[idx])

    # 3) Label texte
    if _class_names and idx < len(_class_names):
        label = _class_names[idx]
    else:
        label = str(idx)

    return label, confidence
