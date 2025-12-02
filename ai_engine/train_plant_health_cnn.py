import os
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.preprocessing import image_dataset_from_directory
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

# === 1. Chemins ===
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets" / "plant_health"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True, parents=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 10  # tu peux augmenter si ton PC supporte


def main():
    print("📂 Chargement du dataset depuis :", DATA_DIR)

    # === 2. Charger les images depuis les dossiers ===
    train_ds = image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
    )
    val_ds = image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
    )

    class_names = train_ds.class_names
    print("🔖 Classes détectées :", class_names)

    # Préfetch pour accélérer
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds_pref = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds_pref = val_ds.prefetch(buffer_size=AUTOTUNE)

    # === 3. Base MobileNetV2 pré-entraînée ===
    base_model = MobileNetV2(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # on gèle la base pour du transfer learning

    # === 4. Construire notre modèle SANS TrueDivide/Subtract ===
    inputs = layers.Input(shape=IMG_SIZE + (3,))

    # 🔁 Normalisation équivalente à preprocess_input :
    #    x = (x / 127.5) - 1  -> dans une vraie couche Keras Rescaling
    x = layers.Rescaling(scale=1.0 / 127.5, offset=-1.0)(inputs)

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(len(class_names), activation="softmax")(x)

    model = models.Model(inputs, outputs)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.summary()

    # === 5. Entraînement ===
    print("🚀 Début de l'entraînement du modèle de santé des plantes…")
    history = model.fit(
        train_ds_pref,
        validation_data=val_ds_pref,
        epochs=EPOCHS,
    )

    # === 6. Sauvegarde du modèle au format .keras ===
    model_path = MODEL_DIR / "plant_health_mobilenet.keras"
    model.save(model_path)
    print(f"✅ Modèle sauvegardé ici : {model_path}")

    # Sauvegarde des noms de classes pour plus tard
    classes_path = MODEL_DIR / "plant_health_classes.txt"
    with open(classes_path, "w", encoding="utf-8") as f:
        for name in class_names:
            f.write(name + "\n")
    print(f"✅ Classes sauvegardées ici : {classes_path}")


if __name__ == "__main__":
    main()
