import redis
import json
import numpy as np
import tensorflow as tf
import joblib
import os
import sys

# Silenciar logs informativos de TensorFlow para mantener la terminal limpia
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Asegurar que el path reconozca la raíz para importar la configuración global
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_BRAIN_PULSE, CH_VOTES

class TalamoVotanteH5:
    def __init__(self):
        """
        Neurona Talamica v3.8: Ahora actúa como clasificador de contexto y votante activo.
        Implementa jerarquía de prioridad: 5 > 3 > 1 (Alcista) y 6 > 4 > 2 (Bajista).
        """
        self.model_path = os.path.join(os.getcwd(), 'modelos', 'talamo_regimenes.h5')
        self.scaler_path = os.path.join(os.getcwd(), 'modelos', 'talamo_scaler.pkl')
        self.features_path = os.path.join(os.getcwd(), 'modelos', 'talamo_features.pkl')

        # Verificación de integridad de archivos de IA
        if not all(os.path.exists(p) for p in [self.model_path, self.scaler_path, self.features_path]):
            print("❌ ERROR CRÍTICO: Faltan archivos del modelo Tálamo en /modelos.")
            sys.exit(1)

        try:
            # 1. Carga de infraestructura neural
            self.model = tf.keras.models.load_model(self.model_path, compile=False)
            self.scaler = joblib.load(self.scaler_path)
            self.features_list = joblib.load(self.features_path)
            
            # 2. Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            self.pubsub.subscribe(CH_MARKET_DATA)
            
            self.EXPERTO_ID = "talamo_v1"
            print(f"--- 🧠 Tálamo H5: Clasificador y VOTANTE ACTIVO ({self.EXPERTO_ID}) ---", flush=True)
        except Exception as e:
            print(f"❌ Error fatal al inicializar el Tálamo: {e}")
            sys.exit(1)

    def calcular_voto_jerarquico(self, regime_id):
        """
        Traduce el régimen detectado en un voto y una confianza (prioridad).
        0: Neutral (0% Conf)
        Alcistas: 1 (33% Conf), 3 (66% Conf), 5 (100% Conf)
        Bajistas: 2 (33% Conf), 4 (66% Conf), 6 (100% Conf)
        """
        # Mapeo de Voto: 1: BUY, -1: SELL, 0: NEUTRAL
        # Mapeo de Confianza: Representa la 'prioridad' solicitada
        
        logic = {
            0: (0, 0.0),    # Lateral
            1: (1, 0.33),   # Alcista Vol Baja
            3: (1, 0.66),   # Alcista Vol Alta
            5: (1, 1.0),    # Tendencia Alcista Fuerte
            2: (-1, 0.33),  # Bajista Vol Baja
            4: (-1, 0.66),  # Bajista Vol Alta
            6: (-1, 1.0)    # Tendencia Bajista Fuerte
        }
        
        return logic.get(regime_id, (0, 0.0))

    def escuchar(self):
        """Bucle de escucha sensorial y emisión de voto por contexto."""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    ts = data.get('Timestamp')
                    
                    # 1. Preparar vector de entrada (19 dimensiones)
                    input_vector = []
                    for col in self.features_list:
                        val = data.get(col, 0.0)
                        input_vector.append(float(val))
                    
                    # 2. Inferencia Neural
                    X_scaled = self.scaler.transform(np.array(input_vector).reshape(1, -1))
                    probs = self.model.predict(X_scaled, verbose=0)[0]
                    
                    # 3. Identificar Régimen Dominante
                    id_dominante = int(np.argmax(probs))
                    conf_ia = float(probs[id_dominante])
                    
                    # 4. Lógica de Votante (Jerarquía Andrés)
                    voto, prioridad = self.calcular_voto_jerarquico(id_dominante)
                    
                    # 5. Emitir Voto al canal democrático (CH_VOTES)
                    # El Ejecutor recibirá este voto como un experto más
                    voto_payload = {
                        "experto_id": self.EXPERTO_ID,
                        "voto": voto,
                        "confianza": prioridad, # Prioridad basada en el ID del régimen
                        "Timestamp": ts,
                        "meta": f"Régimen {id_dominante} detectado con {conf_ia:.1%} de seguridad IA"
                    }
                    self.r.publish(CH_VOTES, json.dumps(voto_payload))

                    # 6. Emitir Pulso de Contexto (CH_BRAIN_PULSE)
                    # Mantenemos esto para que el monitor siga viendo la distribución mental completa
                    distribucion = {f"prob_regimen_{i}": float(p) for i, p in enumerate(probs)}
                    brain_pulse = {
                        "Timestamp": ts,
                        "Close_Price": data.get('Close_Price'),
                        "regime_id": id_dominante,
                        "confidence": round(conf_ia, 3), # Confianza técnica del modelo
                        "regime_distribution": distribucion
                    }
                    self.r.publish(CH_BRAIN_PULSE, json.dumps(brain_pulse))
                    
                except Exception as e:
                    print(f"⚠️ Error en ciclo de inferencia del Tálamo: {e}")

if __name__ == "__main__":
    talamo = TalamoVotanteH5()
    try:
        talamo.escuchar()
    except KeyboardInterrupt:
        print("\n[bold red]🛑 Tálamo Votante detenido por el usuario.[/]")