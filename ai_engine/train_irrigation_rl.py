import os
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.logger import configure
from irrigation_env import IrrigationEnv


# -------------------------
#   Préparation du dossier
# -------------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(CURRENT_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "ppo_irrigation.zip")


# -------------------------
#   Entraînement PPO
# -------------------------

def train_model():

    print("\n🚀 DÉMARRAGE DE L'ENTRAÎNEMENT PPO POUR L’IRRIGATION…\n")

    # On créé l’environnement Gym
    env = DummyVecEnv([lambda: IrrigationEnv(episode_days=60)])

    # Logger propre (facultatif mais pratique pour debug)
    new_logger = configure(os.path.join(CURRENT_DIR, "logs"), ["stdout", "csv", "tensorboard"])

    # Créer le modèle RL PPO (stable-baselines3)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=2.5e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        n_epochs=10,
    )

    model.set_logger(new_logger)

    # Lance l’entraînement — tu peux augmenter le nombre de steps
    model.learn(total_timesteps=100_000)

    # Sauvegarde du modèle
    model.save(MODEL_PATH)

    print(f"\n🎉 Modèle entraîné et sauvegardé ici : {MODEL_PATH}\n")


# -------------------------
#   Test rapide du modèle
# -------------------------

def test_model(n_steps=30):
    if not os.path.exists(MODEL_PATH):
        print("❌ Aucun modèle trouvé. Entraîne-le d'abord.")
        return

    print("\n🔍 TEST DU MODÈLE EN CHARGEANT ppo_irrigation.zip\n")

    env = IrrigationEnv()
    model = PPO.load(MODEL_PATH)

    obs, _ = env.reset()
    for i in range(n_steps):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)

        print(f"Jour {i+1:02d} | Action = {action} | Reward = {reward:.3f} | Humidité = {obs[0]:.2f}")

        if terminated:
            obs, _ = env.reset()

    print("\n✔️ Test terminé.\n")


# -------------------------
#   Exécution principale
# -------------------------

if __name__ == "__main__":
    train_model()
    test_model()
