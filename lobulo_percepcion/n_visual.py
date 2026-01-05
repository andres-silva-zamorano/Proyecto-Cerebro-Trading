import redis
import json
import numpy as np
import tensorflow as tf
import os
import sys

# Asegurar que reconozca la raíz para importar config
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VOTES

# PARÁMETROS DEL TRIAL 15
VENTANA = 45
COLUMNAS_INPUT = [
    'EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320', 
    'DI_Plus', 'DI_Minus', 'ADX_Val', 'RSI_Val', 'MACD_Val', 'ATR_Rel'
]

def main():
    print("[EXPERTO IA VISUAL]: Iniciando carga del Cerebro Alpha...")
    
    # Identidad para la Matriz de Reputación
    EXPERTO_ID = "ia_visual_alpha_v1"

    # 1. Carga del Modelo
    ruta_modelo = os.path.join(os.getcwd(), 'modelos', 'cerebro_hft_alpha.h5')
    if not os.path.exists(ruta_modelo):
        print(f"ERROR: El archivo {ruta_modelo} NO EXISTE.")
        return

    try:
        model = tf.keras.models.load_model(ruta_modelo)
        print(f"Modelo {EXPERTO_ID} cargado exitosamente.")
    except Exception as e:
        print(f"ERROR AL CARGAR EL MODELO: {e}")
        return

    # 2. Conexión a la Médula Espinal (Redis)
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    memoria_velas = []
    print(f"👁️ Experto {EXPERTO_ID} activo. Esperando pulso sensorial...")

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                ts = data.get('Timestamp')
                
                # Extraer indicadores para la IA
                inputs = [data.get(col, 0) for col in COLUMNAS_INPUT]
                memoria_velas.append(inputs)

                # Mantener solo el tamaño de la ventana
                if len(memoria_velas) > VENTANA:
                    memoria_velas.pop(0)

                if len(memoria_velas) == VENTANA:
                    # Preparación de la "foto" para la IA
                    foto = np.array(memoria_velas)
                    
                    # Normalización Z-Score (tal como en el entrenamiento)
                    # $$Z = \frac{x - \mu}{\sigma}$$
                    foto_norm = (foto - np.mean(foto, axis=0)) / (np.std(foto, axis=0) + 1e-8)
                    
                    # Predicción
                    pred = model.predict(foto_norm.reshape(1, VENTANA, len(COLUMNAS_INPUT)), verbose=0)[0]
                    idx_clase = np.argmax(pred)
                    confianza = float(pred[idx_clase])

                    # --- MAPEO AL CONTRATO DE VOTOS ---
                    # Clases originales: 0=Neutral, 1=BUY, 2=SELL
                    voto = 0
                    if idx_clase == 1: voto = 1   # BUY
                    elif idx_clase == 2: voto = -1 # SELL

                    # 3. Construcción del Voto
                    voto_payload = {
                        "experto_id": EXPERTO_ID,
                        "voto": voto,
                        "confianza": round(confianza, 2),
                        "Timestamp": ts,
                        "meta": f"Predicción clase {idx_clase} con {confianza:.2%}"
                    }

                    # 4. Publicación en el canal democrático
                    r.publish(CH_VOTES, json.dumps(voto_payload))
                    
                    if voto != 0:
                        dir_label = "BUY" if voto == 1 else "SELL"
                        print(f"[{ts}] {EXPERTO_ID} votó {dir_label} | Conf: {confianza:.2%}")

            except Exception as e:
                print(f"Error procesando vela en IA Visual: {e}")

if __name__ == "__main__":
    main()