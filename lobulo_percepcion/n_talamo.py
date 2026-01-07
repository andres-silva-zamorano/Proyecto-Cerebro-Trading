import redis, json, sys, os
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_BRAIN_PULSE

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)
    # flush=True asegura que aparezca en el orquestador inmediatamente
    print("--- 🧠 Neurona Talamica Activada: Emitiendo Pulso Crudo ---", flush=True)

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            regimenes = {i: data.get(f'prob_regimen_{i}', 0) for i in range(7)}
            id_dominante = max(regimenes, key=regimenes.get)
            
            brain_pulse = {
                "Timestamp": data.get('Timestamp'),
                "Close_Price": data.get('Close_Price'),
                "regime_id": id_dominante,
                "confidence": regimenes[id_dominante]
            }
            r.publish(CH_BRAIN_PULSE, json.dumps(brain_pulse))

if __name__ == "__main__":
    main()