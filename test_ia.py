import tensorflow as tf
import os

modelo_path = "modelos/cerebro_hft_alpha.h5"

if os.path.exists(modelo_path):
    print(f"Archivo encontrado en {modelo_path}. Cargando...")
    try:
        model = tf.keras.models.load_model(modelo_path)
        print("✅ EXITO: El modelo se cargo correctamente en memoria.")
        print(f"Estructura del modelo: {model.input_shape}")
    except Exception as e:
        print(f"❌ ERROR al cargar el modelo: {e}")
else:
    print(f"❌ ERROR: No se encuentra el archivo en {modelo_path}")