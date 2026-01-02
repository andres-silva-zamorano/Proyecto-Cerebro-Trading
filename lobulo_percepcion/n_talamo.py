import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_BRAIN_STATE

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    print("--- Neurona Talamica Activada: Filtrando Regímenes ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            
            regimenes = {i: data.get(f'prob_regimen_{i}', 0) for i in range(7)}
            id_dominante = max(regimenes, key=regimenes.get)
            prob_dominante = regimenes[id_dominante]
            
            brain_state = {
                "Timestamp": data.get('Timestamp'),
                "Close_Price": data.get('Close_Price'),
                "regime_id": id_dominante,
                "confidence": prob_dominante,
                "is_stable": prob_dominante > 0.65
            }
            
            # USAR PUBLISH EN LUGAR DE SET
            r.publish(CH_BRAIN_STATE, json.dumps(brain_state))
            
            if brain_state["is_stable"]:
                print(f"Tálamo: Régimen {id_dominante} confirmado ({prob_dominante:.2f})")

if __name__ == "__main__":
    main()