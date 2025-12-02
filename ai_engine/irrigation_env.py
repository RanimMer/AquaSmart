import numpy as np
import gymnasium as gym
from gymnasium import spaces


class IrrigationEnv(gym.Env):
    """
    Environnement de simulation réaliste (simplifié) pour l'irrigation.

    Observation (state) = vecteur de 5 valeurs normalisées entre [0, 1] :

      0: soil_moisture      → humidité du sol (0 = très sec, 1 = saturé)
      1: growth_stage       → stade de croissance (0 = semis, 1 = proche récolte)
      2: besoin_norm        → besoin en eau de la culture (basé sur L/j)
      3: rain_norm          → pluie des dernières 24h (0 = aucune, 1 = pluie forte)
      4: temp_norm          → température (0 = 0°C, 1 = 40°C)

    Actions discrètes :
      0: ne pas arroser
      1: arroser un peu
      2: arroser moyen
      3: arroser beaucoup

    Reward (récompense) :
      - on récompense l'humidité dans une zone idéale [0.4, 0.7]
      - on pénalise sol trop sec ou trop humide
      - on pénalise un peu l'eau utilisée (pour économiser)
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, episode_days: int = 60):
        super().__init__()

        # 5 features dans l'observation
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        # 4 actions possibles
        # 0 = rien, 1 = peu, 2 = moyen, 3 = beaucoup
        self.action_space = spaces.Discrete(4)

        # Durée d'un épisode (ex: 60 "jours")
        self.episode_days = episode_days
        self.day = 0

        # Etat interne
        self.soil_moisture = 0.5
        self.growth_stage = 0.0
        self.besoin_norm = 0.5
        self.rain_norm = 0.0
        self.temp_norm = 0.5

    # ---------------------------
    #   Fonctions gym standard
    # ---------------------------

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.day = 0

        # On démarre avec des valeurs "raisonnables"
        self.soil_moisture = float(np.random.uniform(0.3, 0.7))
        self.growth_stage = 0.0

        # besoin en eau: culture peu / moy / très gourmande
        self.besoin_norm = float(np.random.uniform(0.2, 0.8))

        # météo initiale
        self.rain_norm, self.temp_norm = self._simulate_weather()

        obs = self._get_obs()
        return obs, {}

    def step(self, action):
        """
        action ∈ {0,1,2,3}
        On simule une journée :
          - l'agent décide combien arroser
          - la météo apporte pluie + température
          - le sol perd de l'eau par évaporation
          - on calcule la reward
        """
        self.day += 1

        # --------- 1) Quantité d'eau ajoutée par l'action ---------
        # On imagine que 0.3 correspond à "arrosage très fort" en échelle normalisée.
        water_amounts = [0.0, 0.10, 0.20, 0.30]
        water_added = water_amounts[int(action)]

        # --------- 2) Nouvelle météo du jour (pluie + température) ---------
        self.rain_norm, self.temp_norm = self._simulate_weather()

        # convertir pluie (0-1) en effet sur humidité du sol
        rain_effect = self.rain_norm * 0.25  # 25% max d'augmentation

        # --------- 3) Mise à jour de l'humidité du sol ---------
        # Ajout d'eau (action + pluie)
        self.soil_moisture += water_added + rain_effect

        # Evaporation (dépend de la température et du stade de croissance)
        # plus il fait chaud & plus la culture est développée, plus ça consomme
        base_evap = 0.05
        temp_factor = self.temp_norm * 0.08
        growth_factor = self.growth_stage * 0.05
        evap = base_evap + temp_factor + growth_factor

        self.soil_moisture -= evap

        # On sature entre 0 et 1
        self.soil_moisture = float(np.clip(self.soil_moisture, 0.0, 1.0))

        # --------- 4) Mise à jour du stade de croissance ---------
        # simple modèle linéaire : 0 → 1 sur la durée de l'épisode
        self.growth_stage = float(
            np.clip(self.day / self.episode_days, 0.0, 1.0)
        )

        # --------- 5) Calcul de la récompense ---------
        reward = self._compute_reward(self.soil_moisture, water_added)

        # --------- 6) Fin d'épisode ---------
        terminated = self.day >= self.episode_days
        truncated = False

        obs = self._get_obs()
        info = {}

        return obs, reward, terminated, truncated, info

    # ---------------------------
    #   Helpers internes
    # ---------------------------

    def _get_obs(self):
        """Construit le vecteur d'observation normalisé."""
        return np.array(
            [
                self.soil_moisture,
                self.growth_stage,
                self.besoin_norm,
                self.rain_norm,
                self.temp_norm,
            ],
            dtype=np.float32,
        )

    def _simulate_weather(self):
        """
        Simule météo du jour:
          - pluie: mostly dry, parfois orage.
          - température: entre 10 et 35°C, normalisée sur 0–1.
        """
        # 80% du temps peu/pas de pluie, 20% du temps pluie plus forte
        if np.random.rand() < 0.8:
            rain_mm = np.random.exponential(scale=1.0)  # petites pluies
        else:
            rain_mm = np.random.uniform(5.0, 30.0)      # grosse pluie / orage

        rain_mm = float(np.clip(rain_mm, 0.0, 40.0))       # bornes
        rain_norm = rain_mm / 40.0                         # 40mm -> 1.0

        # température en °C entre 10 et 35
        temp_c = float(np.random.uniform(10.0, 35.0))
        temp_norm = (temp_c / 40.0)  # 40°C -> 1.0

        return rain_norm, temp_norm

    def _compute_reward(self, soil_moisture, water_added):
        """
        Reward réaliste mais simple :
          - bonus max si humidité dans [0.45, 0.65]
          - pénalité si trop sec (<0.25) ou trop humide (>0.85)
          - petite pénalité sur l'eau utilisée pour encourager l'économie
        """
        reward = 0.0

        # zone idéale
        if 0.45 <= soil_moisture <= 0.65:
            reward += 1.0
        # zone "acceptable"
        elif 0.35 <= soil_moisture <= 0.75:
            reward += 0.2
        else:
            # trop sec ou trop humide
            reward -= 1.0

        # coût de l'eau (gaspillage)
        reward -= water_added * 0.4

        # petit bonus supplémentaire si proche du centre 0.55
        reward -= abs(soil_moisture - 0.55) * 0.5

        return float(reward)

    def render(self):
        print(
            f"Jour {self.day:02d} | "
            f"Humidité sol = {self.soil_moisture:.2f} | "
            f"Croissance = {self.growth_stage:.2f} | "
            f"Pluie = {self.rain_norm:.2f} | "
            f"T° = {self.temp_norm:.2f}"
        )
