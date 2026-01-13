import redis
import json
import numpy as np
import tensorflow as tf
import joblib
import os
import sys

# Silenciar logs informativos de TensorFlow para mantener la terminal limpia
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Asegurar importación de la configuración global desde la raíz del proyecto
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_BRAIN_PULSE, CH_VOTES

class TalamoFractalv39:
    def __init__(self):
        """
        Tálamo Fractal v3.9.2.
        Realiza inferencia dual diferenciada para eliminar el sesgo de resolución:
        - M1 (Operativo): Inferencia rápida sobre el flujo PubSub de 1 minuto.
        - M15 (Estructural): Inferencia macro consultando el caché Redis 'htf_context_data'.
        """
        try:
            # 1. Carga de infraestructura neural de 1 Minuto (Presente Operativo)
            self.model_m1 = tf.keras.models.load_model('modelos/talamo_regimenes.h5', compile=False)
            self.scaler_m1 = joblib.load('modelos/talamo_scaler.pkl')
            self.features_list = joblib.load('modelos/talamo_features.pkl')

            # 2. Carga de infraestructura neural de 15 Minutos (Estructura Fractal)
            # Este modelo fue entrenado con datos consolidados para filtrar el ruido micro.
            self.model_htf = tf.keras.models.load_model('modelos/talamo_regimenes_HTF.h5', compile=False)
            self.scaler_htf = joblib.load('modelos/talamo_scaler_HTF.pkl')

            # 3. Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            self.pubsub.subscribe(CH_MARKET_DATA)
            
            print(f"--- 🧠 Tálamo Fractal v3.9.2: Inferencia Diferenciada ACTIVA ---")
            print(f"📡 Monitoreando M1 (Real-time) y M15 (Caché Estructural)...")
        except Exception as e:
            print(f"❌ Error crítico inicializando Tálamo Fractal: {e}")
            sys.exit(1)

    def escuchar(self):
        """
        Bucle de procesamiento síncrono. 
        Dispara la inferencia dual cada vez que llega un tick de 1 minuto.
        """
        for message in self.pubsub.listen():
            if message['type'] != 'message':
                continue
                
            try:
                # Datos frescos de 1 minuto (Trigger del sistema)
                data_m1 = json.loads(message['data'])
                ts = data_m1.get('Timestamp')
                
                # --- A. INFERENCIA MICRO (Modelo 1M) ---
                # Extraemos el vector de indicadores procesado por el Feeder en resolución M1
                input_v_m1 = [float(data_m1.get(col, 0.0)) for col in self.features_list]
                X_m1_raw = np.array(input_v_m1).reshape(1, -1)
                X_m1_scaled = self.scaler_m1.transform(X_m1_raw)
                
                probs_m1 = self.model_m1.predict(X_m1_scaled, verbose=0)[0]
                id_m1 = int(np.argmax(probs_m1))

                # --- B. INFERENCIA ESTRUCTURAL (Modelo 15M Real) ---
                # Obtenemos los indicadores calculados sobre velas de 15m desde Redis.
                # Esto es lo que rompe el efecto espejo y permite un filtrado macro real.
                htf_raw = self.r.get("htf_context_data")
                
                if htf_raw:
                    data_htf = json.loads(htf_raw)
                    # Usamos la misma lista de features pero con los valores de resolución M15
                    input_v_htf = [float(data_htf.get(col, 0.0)) for col in self.features_list]
                    X_htf_raw = np.array(input_v_htf).reshape(1, -1)
                    X_htf_scaled = self.scaler_htf.transform(X_htf_raw)
                    
                    probs_htf = self.model_htf.predict(X_htf_scaled, verbose=0)[0]
                    id_htf = int(np.argmax(probs_htf))
                else:
                    # Fallback si el sistema acaba de arrancar y no hay data HTF aún
                    id_htf = 0

                # 3. Publicar Pulso Dual para el Ejecutor y el Monitor Alpha
                # id_m1 e id_htf ahora representan estados temporales REALMENTE distintos.
                self.r.publish(CH_BRAIN_PULSE, json.dumps({
                    "Timestamp": ts,
                    "Close_Price": data_m1.get('Close_Price'),
                    "regime_id": id_m1,      # Micro-estado (1 Minuto)
                    "regime_htf": id_htf,    # Macro-estado (15 Minutos)
                    "confidence_m1": round(float(probs_m1[id_m1]), 3)
                }))

                # 4. Emitir Voto Democrático al Comité (Basado en el marco M1)
                # El Ejecutor recibirá este voto y lo validará contra el 'regime_htf' fractal.
                voto_direccional = 0
                if id_m1 in [1, 3, 5]: voto_direccional = 1   # Alcista
                elif id_m1 in [2, 4, 6]: voto_direccional = -1 # Bajista
                
                # Confianza basada en la jerarquía de intensidad del régimen micro
                confianza_voto = 1.0 if id_m1 in [5, 6] else (0.66 if id_m1 in [3, 4] else 0.33)
                
                self.r.publish(CH_VOTES, json.dumps({
                    "experto_id": "talamo_v1",
                    "voto": voto_direccional,
                    "confianza": confianza_voto,
                    "Timestamp": ts,
                    "meta": f"Fractal: M1(R{id_m1}) vs M15(R{id_htf})"
                }))

            except Exception as e:
                print(f"⚠️ Error en ciclo de procesamiento Tálamo Fractal: {e}")

if __name__ == "__main__":
    talamo = TalamoFractalv39()
    try:
        talamo.escuchar()
    except KeyboardInterrupt:
        print("\n🛑 Lóbulo Talamico Fractal v3.9.2 detenido por el usuario.")