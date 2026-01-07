import redis, json, os, sys
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_VESTIBULAR, CH_VOTES

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_VESTIBULAR)
    print("--- 🛡️ Guardián Vestibular: Filtro de Ruido Inteligente ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            es_estable = data.get('is_stable', True)
            
            # SOLO enviamos voto si hay RUIDO ALTO para frenar al Ejecutor
            if not es_estable:
                voto_payload = {
                    "experto_id": "guardian_vestibular_v1",
                    "voto": 0, # Señal de PARE
                    "confianza": 1.0,
                    "Timestamp": data.get('Timestamp')
                }
                r.publish(CH_VOTES, json.dumps(voto_payload))
            else:
                # Si el mercado vuelve a ser estable, enviamos un voto Neutral (1)
                # que no activa la multiplicación por 0.1 en el ejecutor
                voto_payload = {
                    "experto_id": "guardian_vestibular_v1",
                    "voto": 1, 
                    "confianza": 0.0,
                    "Timestamp": data.get('Timestamp')
                }
                r.publish(CH_VOTES, json.dumps(voto_payload))

if __name__ == "__main__": main()