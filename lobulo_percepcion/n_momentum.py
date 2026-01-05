import redis
import json
import os
import sys

sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VOTES

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    # Identificador único para el sistema de reputación
    # Si creas otro archivo, cámbiale este ID a "momentum_v2"
    EXPERTO_ID = "momentum_v1"

    print(f"--- ⚡ Experto Momentum Activo: {EXPERTO_ID} ---")

    # Memoria simple para detectar dirección
    precio_anterior = None

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            
            precio_actual = data.get('Close_Price', 0)
            adx = data.get('ADX_Val', 0)
            rsi = data.get('RSI_Val', 50)
            
            # 1. Lógica de Dirección (¿Hacia dónde va la fuerza?)
            voto = 0
            confianza = 0.0
            
            if precio_anterior is not None:
                # Si hay tendencia fuerte (ADX > 25)
                if adx > 25:
                    if precio_actual > precio_anterior and rsi > 50:
                        voto = 1  # Voto COMPRA
                        confianza = adx / 100 # La confianza escala con el ADX
                    elif precio_actual < precio_anterior and rsi < 50:
                        voto = -1 # Voto VENTA
                        confianza = adx / 100
                
            # 2. Contrato de Comunicación de Expertos
            voto_payload = {
                "experto_id": EXPERTO_ID,
                "voto": voto,
                "confianza": round(confianza, 2),
                "Timestamp": data.get('Timestamp')
            }
            
            # Publicar voto en el canal democrático
            r.publish(CH_VOTES, json.dumps(voto_payload))
            
            # Actualizar memoria
            precio_anterior = precio_actual
            
            if voto != 0:
                dir_label = "BUY" if voto == 1 else "SELL"
                print(f"🗳️ {EXPERTO_ID} votó {dir_label} | Conf: {confianza:.2f}")

if __name__ == "__main__":
    main()