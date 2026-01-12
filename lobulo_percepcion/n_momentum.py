import redis, json, os, sys
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VOTES

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    EXPERTO_ID = "momentum_v1"
    print(f"--- ⚡ Experto Momentum Activo: {EXPERTO_ID} ---")

    precio_anterior = None
    ultimo_ts_procesado = None

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            ts = data.get('Timestamp')
            
            # PROTECCIÓN CONTRA SPAM: Solo un voto por vela nueva
            if ts == ultimo_ts_procesado:
                continue
            
            precio_actual = data.get('Close_Price', 0)
            adx = data.get('ADX_Val', 0)
            rsi = data.get('RSI_Val', 50)
            
            voto, confianza = 0, 0.0
            
            if precio_anterior is not None and adx > 25:
                if precio_actual > precio_anterior and rsi > 50:
                    voto, confianza = 1, adx / 100
                elif precio_actual < precio_anterior and rsi < 50:
                    voto, confianza = -1, adx / 100
                
            r.publish(CH_VOTES, json.dumps({
                "experto_id": EXPERTO_ID, "voto": voto,
                "confianza": round(confianza, 2), "Timestamp": ts
            }))
            
            precio_anterior = precio_actual
            ultimo_ts_procesado = ts

if __name__ == "__main__": main()