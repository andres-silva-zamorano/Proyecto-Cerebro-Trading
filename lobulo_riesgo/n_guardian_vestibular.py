import redis
import json
import os
import sys

sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_VESTIBULAR, CH_VOTES

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_VESTIBULAR)

    EXPERTO_ID = "guardian_vestibular_v1"
    print(f"--- 🛡️ Guardián de Riesgo Activo: {EXPERTO_ID} ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            
            es_estable = data.get('is_stable', True)
            ruido = data.get('noise_level', 0.0)
            
            # LÓGICA DE PROTECCIÓN:
            # Si el mercado es inestable, enviamos un voto Neutral (0)
            # con confianza total para frenar a los expertos agresivos.
            voto = 0 
            confianza = 1.0 if not es_estable else 0.0

            voto_payload = {
                "experto_id": EXPERTO_ID,
                "voto": voto,
                "confianza": confianza,
                "Timestamp": data.get('Timestamp'),
                "meta": f"Ruido: {ruido:.6f} | Estable: {es_estable}"
            }

            r.publish(CH_VOTES, json.dumps(voto_payload))
            
            if not es_estable:
                print(f"⚠️ {EXPERTO_ID} emitiendo VETO por ruido alto ({ruido:.6f})")

if __name__ == "__main__":
    main()