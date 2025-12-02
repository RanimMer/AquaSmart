import os
from datetime import date
import numpy as np
from stable_baselines3 import PPO

from irrigation_env import IrrigationEnv  # juste pour garder la même structure d'observation

# Chemin du modèle entraîné
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "models", "ppo_irrigation.zip")

# Cache global pour ne pas recharger le modèle à chaque appel
_model = None


def _get_model():
    """
    Charge le modèle PPO une seule fois et le garde en mémoire.
    """
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(
                f"Modèle RL introuvable à {MODEL_PATH}. "
                f"Entraîne-le d'abord avec train_irrigation_rl.py."
            )
        _model = PPO.load(MODEL_PATH)
    return _model


def _build_observation_from_context(culture, meteo=None):
    """
    Construit le vecteur d'observation de taille 5 attendu par IrrigationEnv,
    à partir d'une instance de Culture (+ éventuellement dernière mesure météo).
    """

    # 0) Humidité du sol (on n'a pas la vraie valeur → on prend une heuristique)
    #    Pour l'instant, on supposera un niveau moyen.
    soil_moisture = 0.5

    # 1) Stade de croissance (0 = semis, 1 = proche récolte)
    if culture.date_semis and culture.date_recolte_prevue:
        total_days = (culture.date_recolte_prevue - culture.date_semis).days
        passed_days = (date.today() - culture.date_semis).days

        if total_days > 0:
            growth_stage = passed_days / total_days
        else:
            growth_stage = 0.0

        growth_stage = float(np.clip(growth_stage, 0.0, 1.0))
    else:
        growth_stage = 0.5

    # 2) Besoin normalisé (on divise par 10L/j comme échelle grossière)
    besoin = float(culture.besoin_base_l_j or 0.0)
    besoin_norm = besoin / 10.0
    besoin_norm = float(np.clip(besoin_norm, 0.0, 1.0))

    # 3) Pluie normalisée (si on a une station météo)
    rain_norm = 0.0
    temp_norm = 0.5

    if meteo is not None:
        # ⚠️ adapte ces noms de champs à ton modèle StationMeteo
        rain_mm = float(getattr(meteo, "rain_mm_24h", 0.0))
        temp_c = float(getattr(meteo, "temperature_c", 20.0))

        rain_norm = float(np.clip(rain_mm / 40.0, 0.0, 1.0))
        temp_norm = float(np.clip(temp_c / 40.0, 0.0, 1.0))

    obs = np.array(
        [soil_moisture, growth_stage, besoin_norm, rain_norm, temp_norm],
        dtype=np.float32,
    )
    return obs


# mapping action RL -> "fréquence d'arrosage en jours"
ACTION_TO_FREQUENCY = {
    0: 4,  # ne pas arroser => on espace plus
    1: 3,  # peu d'eau
    2: 2,  # moyen
    3: 1,  # beaucoup
}


def recommander_frequence_irrigation(culture, meteo=None):
    """
    Prend une Culture (+ éventuellement une mesure météo),
    renvoie (frequence_en_jours, action_rl).
    """
    model = _get_model()
    obs = _build_observation_from_context(culture, meteo=meteo)

    action, _ = model.predict(obs, deterministic=True)
    action_int = int(action)

    freq = ACTION_TO_FREQUENCY.get(action_int, 3)

    return freq, action_int
