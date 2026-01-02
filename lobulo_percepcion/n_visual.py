import redis
import json
import numpy as np
import tensorflow as tf
import os
import sys

# Forzar que vea la raíz para el import de config
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VISUAL

VENTANA = 45
COLUMNAS_INPUT = ['EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320', 
                  'DI_Plus', 'DI_Minus', 'ADX_Val', 'RSI_Val', 'MACD_Val', 'ATR_Rel']

def main():
    print("🧠 Neurona Visual AI: Iniciando carga del Cerebro Alpha...")
    
    # RUTA ABSOLUTA AUTOMÁTICA
    ruta_modelo = os.path.join(os.getcwd(), 'modelos', 'cerebro_hft_alpha.h5')
    print(f"📂 Buscando modelo en: {ruta_modelo}")

    if not os.path.exists(ruta_modelo):
        print(f"❌ ERROR: El archivo {ruta_modelo} NO EXISTE.")
        return

    try:
        model = tf.keras.models.load_model(ruta_modelo)
        print("✅ Cerebro Alpha cargado exitosamente en memoria.")
    except Exception as e:
        print(f"❌ ERROR AL CARGAR EL MODELO: {e}")
        return
    
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        pubsub = r.pubsub()
        pubsub.subscribe(CH_MARKET_DATA)
        print(f"🔌 Conectado a Redis. Escuchando canal: {CH_MARKET_DATA}")
    except Exception as e:
        print(f"❌ ERROR DE REDIS: {e}")
        return

    memoria_velas = []
    print("👁️ Visual AI activa. Esperando pulso sensorial...")

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                inputs = [data.get(col, 0) for col in COLUMNAS_INPUT]
                memoria_velas.append(inputs)

                if len(memoria_velas) > VENTANA:
                    memoria_velas.pop(0)

                if len(memoria_velas) == VENTANA:
                    foto = np.array(memoria_velas)
                    foto_norm = (foto - np.mean(foto, axis=0)) / (np.std(foto, axis=0) + 1e-8)
                    
                    pred = model.predict(foto_norm.reshape(1, VENTANA, len(COLUMNAS_INPUT)), verbose=0)[0]
                    idx_accion = np.argmax(pred)
                    confianza = float(pred[idx_accion])
                    
                    labels = ["neutral", "bullish_alpha", "bearish_alpha"]
                    fan_order = labels[idx_accion]

                    visual_payload = {
                        "Timestamp": data.get('Timestamp'),
                        "fan_order": fan_order,
                        "confidence": confianza,
                        "action_potential": round(confianza if fan_order != "neutral" else 0, 2)
                    }

                    r.publish(CH_VISUAL, json.dumps(visual_payload))
            except Exception as e:
                print(f"⚠️ Error procesando vela: {e}")

if __name__ == "__main__":
    main()