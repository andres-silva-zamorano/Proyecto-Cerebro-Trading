import redis
import json
import os
import sys

# Asegurar que reconozca la raíz para importar la configuración
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VOTES

def main():
    # 1. Conexión a la Médula Espinal (Redis)
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    # 2. IDENTIDAD ÚNICA (Crucial para la Matriz de Pesos)
    # Cambia este ID para cada nuevo experto que crees
    EXPERTO_ID = "nombre_unico_del_experto_v1"

    print(f"--- 🚀 Experto Activo: {EXPERTO_ID} ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            # Extraer datos del mercado
            data = json.loads(message['data'])
            ts = data.get('Timestamp')
            
            # =====================================================
            # 🧠 AQUÍ VA TU LÓGICA (IA, Técnico, Noticias, LLM...)
            # =====================================================
            # Ejemplo simple:
            # si rsi > 70 -> voto = -1
            # si rsi < 30 -> voto = 1
            # sino -> voto = 0
            
            voto_final = 0       # 1: BUY, -1: SELL, 0: NEUTRAL
            confianza_local = 0.0 # 0.0 a 1.0 (Qué tan seguro estás)
            # =====================================================

            # 3. CONTRATO DE COMUNICACIÓN (El estándar)
            voto_payload = {
                "experto_id": EXPERTO_ID,
                "voto": voto_final,
                "confianza": round(confianza_local, 2),
                "Timestamp": ts,
                "meta": "Opcional: Breve razón del voto" 
            }

            # 4. EMISIÓN DEL VOTO
            r.publish(CH_VOTES, json.dumps(voto_payload))

            if voto_final != 0:
                print(f"🗳️ [{ts}] {EXPERTO_ID} votó {'BUY' if voto_final==1 else 'SELL'}")

if __name__ == "__main__":
    main()